"""PAMR: educational slotted mesh simulator. Python 3.10+, no dependencies.

Read MODEL.md before interpreting the numbers as wireless-network evidence.
"""
from __future__ import annotations

from collections import Counter, deque
from dataclasses import asdict, dataclass, field
import hashlib
import math
import random
import statistics

ALGORITHMS = ("shortest", "reactive", "predictive")
LABELS = {"shortest": "Shortest-hop", "reactive": "Reactive energy-aware",
          "predictive": "Predictive adaptive (PAMR)"}


@dataclass
class Config:
    nodes: int = 30                 # sensors; gateway is additional node 0
    duration: int = 400             # seconds; 1 second = 1 simulation slot
    seed: int = 42
    scenario: str = "burst"         # steady, burst, failure
    traffic: float = 0.03           # Bernoulli generation probability / sensor / slot
    radius: float = 32.0            # coordinate units, not calibrated metres
    horizon: int = 40
    alpha: float = 0.35
    initial_energy: float = 100.0   # illustrative energy units (EU), not joules
    tx_cost: float = 0.10
    rx_cost: float = 0.05
    idle_cost: float = 0.005
    control_tx_cost: float = 0.02
    control_rx_cost: float = 0.005
    advertise_every: int = 10
    decide_every: int = 5
    queue_limit: int = 20
    max_attempts: int = 3           # per hop, including initial attempt
    ttl: int = 100                 # seconds in network
    hysteresis: float = 0.06        # absolute normalized score improvement

    def validate(self):
        if not 8 <= self.nodes <= 100:
            raise ValueError("nodes must be between 8 and 100")
        if not 50 <= self.duration <= 2000:
            raise ValueError("duration must be between 50 and 2000")
        if not 0 < self.traffic <= 0.5:
            raise ValueError("traffic must be in (0, 0.5]")
        if not 15 <= self.radius <= 100:
            raise ValueError("radius must be between 15 and 100")
        if not 1 <= self.horizon <= self.duration:
            raise ValueError("horizon must be between 1 and duration")
        if not 0 < self.alpha <= 1:
            raise ValueError("alpha must be in (0, 1]")
        if self.scenario not in ("steady", "burst", "failure"):
            raise ValueError("unknown scenario")
        if not 10 <= self.initial_energy <= 1000:
            raise ValueError("initial_energy must be between 10 and 1000")
        for name in ("tx_cost", "rx_cost", "idle_cost", "control_tx_cost", "control_rx_cost"):
            if not math.isfinite(getattr(self, name)) or getattr(self, name) < 0:
                raise ValueError(f"{name} must be finite and nonnegative")
        if not 1 <= self.advertise_every <= 100 or not 1 <= self.decide_every <= 100:
            raise ValueError("control and decision intervals must be in [1, 100]")
        if not 1 <= self.max_attempts <= 10 or not 1 <= self.queue_limit <= 1000:
            raise ValueError("invalid retry or queue limit")
        if not 1 <= self.ttl <= 2000 or not 0 <= self.hysteresis <= 1:
            raise ValueError("invalid TTL or hysteresis")


def sample(seed, *parts):
    """Stateless random draw: routes cannot perturb later offered traffic or links."""
    raw = ":".join(map(str, (seed, *parts))).encode()
    return int.from_bytes(hashlib.blake2b(raw, digest_size=8).digest(), "big") / 2**64


def levels_for(count, links):
    neighbors = {i: [] for i in range(count)}
    for a, b, _ in links:
        neighbors[a].append(b)
        neighbors[b].append(a)
    levels = {0: 0}
    q = deque([0])
    while q:
        a = q.popleft()
        for b in sorted(neighbors[a]):
            if b not in levels:
                levels[b] = levels[a] + 1
                q.append(b)
    return levels, neighbors


def make_topology(c):
    rng = random.Random(c.seed)
    # Anchor relays provide a visible mesh, with a deliberately weak relay 1.
    anchors = [(50, 4), (35, 27), (65, 27), (20, 48), (50, 48), (80, 48),
               (22, 72), (50, 72), (78, 72)]
    for _ in range(200):
        positions = anchors[:c.nodes + 1]
        positions += [(rng.uniform(6, 94), rng.uniform(35, 96))
                      for _ in range(c.nodes + 1 - len(positions))]
        links = []
        for a in range(len(positions)):
            for b in range(a + 1, len(positions)):
                d = math.dist(positions[a], positions[b])
                if d <= c.radius:
                    # Known, fixed per-link success estimates, shared by all strategies.
                    p = max(0.65, min(0.99, 0.98 - 0.18 * (d / c.radius)**2
                                     + 0.04 * (sample(c.seed, "quality", a, b) - 0.5)))
                    links.append((a, b, p))
        levels, neighbors = levels_for(c.nodes + 1, links)
        if len(levels) == c.nodes + 1:
            return positions, links, levels, neighbors
    raise ValueError("Could not make a connected topology. Increase radio radius.")


@dataclass
class Observation:
    energy: float
    capacity: float
    drain: float
    queue: int
    at: int
    alive: bool


@dataclass
class Node:
    id: int
    x: float
    y: float
    level: int
    capacity: float
    energy: float
    alive: bool = True
    parent: int | None = None
    drain: float = 0.0
    last_energy: float = 0.0
    queue: deque = field(default_factory=deque)
    observations: dict = field(default_factory=dict)
    spent: Counter = field(default_factory=Counter)
    death: int | None = None
    failure: str | None = None


@dataclass
class Packet:
    id: int
    source: int
    born: int
    hops: int = 0
    attempts: int = 0


class Simulation:
    def __init__(self, config=None, algorithm="predictive"):
        self.c = config or Config()
        self.c.validate()
        if algorithm not in ALGORITHMS:
            raise ValueError("unknown algorithm")
        self.algorithm = algorithm
        positions, self.links, levels, self.neighbors = make_topology(self.c)
        self.quality = {(min(a, b), max(a, b)): p for a, b, p in self.links}
        self.nodes = []
        for i, (x, y) in enumerate(positions):
            capacity = self.c.initial_energy * (0.85 + 0.3 * sample(self.c.seed, "battery", i))
            if i == 1:
                capacity = self.c.initial_energy * 0.38
            if i == 0:
                capacity = 0.0  # gateway is externally powered, excluded from battery stats
            self.nodes.append(Node(i, x, y, levels[i], capacity, capacity, last_energy=capacity))
        self.t = 0
        self.offered = self.generated = self.delivered = self.unavailable = 0
        self.tx_attempts = self.control_messages = self.control_receptions = 0
        self.drops = Counter()
        self.delays = []
        self.hops = []
        self.events = []
        self.snapshots = []
        self.inbox = []             # delivered to next node at next slot boundary
        self.route_changes = 0
        self.forecasts = {}         # due time -> list[(id, forecast)]
        self.prediction_errors = []
        self.prediction_errors_normalized = []

    def log(self, kind, **values):
        self.events.append({"time": self.t, "type": kind, **values})

    def spend(self, n, amount, category):
        if n.id == 0:
            return True
        if not n.alive:
            return False
        enough = n.energy >= amount
        used = min(n.energy, amount)
        n.energy = max(0.0, n.energy - used)
        n.spent[category] += used
        if n.energy <= 1e-9:
            n.energy = 0.0
            n.alive = False
            n.death = self.t
            n.failure = "battery"
            self.log("battery_depleted", node=n.id)
        return enough

    def link_quality(self, a, b):
        return self.quality[(min(a, b), max(a, b))]

    def score(self, n, candidate):
        if candidate == 0:
            return 0.0
        obs = n.observations[candidate]
        # Both energy-aware strategies use last advertised values. Only PAMR
        # projects the energy forward from that observation.
        lookahead = self.c.horizon + self.t - obs.at if self.algorithm == "predictive" else 0
        future_fraction = max(0.0, obs.energy - lookahead * obs.drain) / obs.capacity
        energy_risk = 1 - min(1.0, future_fraction)
        link_loss = 1 - self.link_quality(n.id, candidate)
        queue_fraction = min(1.0, obs.queue / self.c.queue_limit)
        return 0.65 * energy_risk + 0.20 * link_loss + 0.15 * queue_fraction

    def candidates(self, n):
        # Fixed initial BFS level is a strict decreasing potential, guaranteeing
        # loop-free forwarding. No global live-battery information is consulted.
        return [j for j in self.neighbors[n.id]
                if self.nodes[j].level < n.level
                and j in n.observations
                and n.observations[j].alive
                and self.t - n.observations[j].at <= 2 * self.c.advertise_every]

    def choose_parent(self, n):
        eligible = self.candidates(n)
        old = n.parent
        if not eligible:
            best = None
            reason = "No fresh lower-level neighbor advertisement"
        elif self.algorithm == "shortest":
            best = min(eligible, key=lambda j: (self.nodes[j].level,
                                                -self.link_quality(n.id, j), j))
            reason = "Shortest-hop scaffold; highest link success breaks ties"
        else:
            best = min(eligible, key=lambda j: (self.score(n, j), j))
            if old in eligible and self.score(n, old) - self.score(n, best) <= self.c.hysteresis:
                best = old
            reason = ("Lower predicted-energy/link/queue cost" if self.algorithm == "predictive"
                      else "Lower current-energy/link/queue cost")
        n.parent = best
        if old != best:
            if old is not None:
                self.route_changes += 1
            self.log("route_change", node=n.id, old=old, new=best, reason=reason,
                     old_cost=round(self.score(n, old), 4) if old in eligible and self.algorithm != "shortest" else None,
                     new_cost=round(self.score(n, best), 4) if best is not None and self.algorithm != "shortest" else None)
            # Retry limit counts consecutive attempts on the currently selected link.
            if n.queue:
                n.queue[0].attempts = 0

    def advertise(self):
        # Simultaneous snapshots, followed by broadcast delivery; successful
        # advertisements are lossy. Every listener pays reception energy.
        messages = {}
        for n in self.nodes:
            if n.alive:
                if n.id and not self.spend(n, self.c.control_tx_cost, "control_tx"):
                    continue
                if not n.alive:
                    continue
                self.control_messages += 1
                messages[n.id] = Observation(n.energy, n.capacity, n.drain, len(n.queue), self.t, True)
        for sender, obs in messages.items():
            for receiver in self.neighbors[sender]:
                n = self.nodes[receiver]
                if not n.alive:
                    continue
                self.control_receptions += 1
                enough = self.spend(n, self.c.control_rx_cost, "control_rx")
                if enough and n.alive and sample(self.c.seed, "advert", self.t, sender, receiver) < self.link_quality(sender, receiver):
                    n.observations[sender] = obs

    def receive_inbox(self):
        incoming, self.inbox = self.inbox, []
        for target, packet in incoming:
            n = self.nodes[target]
            if target == 0:
                self.delivered += 1
                self.delays.append(self.t - packet.born)
                self.hops.append(packet.hops)
            elif not n.alive:
                self.drops["receiver_offline"] += 1
            elif len(n.queue) >= self.c.queue_limit:
                self.drops["queue_full"] += 1
            else:
                n.queue.append(packet)

    def generate(self):
        c = self.c
        burst_active = c.scenario == "burst" and c.duration // 3 <= self.t < 2 * c.duration // 3
        for n in self.nodes[1:]:
            probability = min(0.95, c.traffic * (3.0 if burst_active else 1.0))
            if sample(c.seed, "traffic", self.t, n.id) < probability:
                self.offered += 1
                if not n.alive:
                    self.unavailable += 1
                    continue
                self.generated += 1
                p = Packet(self.offered, n.id, self.t)
                if len(n.queue) >= c.queue_limit:
                    self.drops["queue_full"] += 1
                else:
                    n.queue.append(p)

    def forward(self):
        # Each sensor gets one attempt per slot. Successful packets enter the
        # next slot's inbox, so no accidental instant multi-hop forwarding occurs.
        for n in self.nodes[1:]:
            if not n.alive:
                while n.queue:
                    n.queue.popleft()
                    self.drops["node_offline"] += 1
                continue
            while n.queue and self.t - n.queue[0].born >= self.c.ttl:
                n.queue.popleft()
                self.drops["ttl_expired"] += 1
            if not n.queue:
                continue
            p = n.queue[0]
            if n.parent is None:
                # Hold queued data until a fresh advertisement yields a route or TTL expires.
                continue
            target = self.nodes[n.parent]
            self.tx_attempts += 1
            p.attempts += 1
            powered = self.spend(n, self.c.tx_cost, "data_tx")
            receiving = powered and target.alive and self.spend(target, self.c.rx_cost, "data_rx")
            success = (powered and receiving and sample(self.c.seed, "data", self.t, n.id,
                       target.id, p.id, p.attempts) < self.link_quality(n.id, target.id))
            if success:
                n.queue.popleft()
                p.hops += 1
                p.attempts = 0
                self.inbox.append((target.id, p))
            elif not powered or p.attempts >= self.c.max_attempts:
                n.queue.popleft()
                self.drops["tx_energy" if not powered else "retry_limit"] += 1

    def update_predictor(self):
        for n in self.nodes[1:]:
            observed = max(0.0, n.last_energy - n.energy) / self.c.decide_every
            n.drain = self.c.alpha * observed + (1 - self.c.alpha) * n.drain
            n.last_energy = n.energy
        # Forecasts are evaluated on the actual subsequent path of this run.
        # Routing can change future drain, so this is NOT a counterfactual test.
        for n in self.nodes[1:]:
            if n.alive:
                due = self.t + self.c.horizon
                if due <= self.c.duration:
                    self.forecasts.setdefault(due, []).append((n.id, max(0.0, n.energy - n.drain * self.c.horizon)))

    def evaluate_forecasts(self):
        for node_id, value in self.forecasts.pop(self.t, []):
            n = self.nodes[node_id]
            if n.failure != "injected":
                error = abs(value - n.energy)
                self.prediction_errors.append(error)
                self.prediction_errors_normalized.append(error / n.capacity)

    def snapshot(self):
        sensors = self.nodes[1:]
        remaining = sum(n.energy for n in sensors)
        self.snapshots.append({
            "time": self.t, "generated": self.generated, "offered": self.offered,
            "delivered": self.delivered, "dropped": sum(self.drops.values()),
            "unavailable": self.unavailable, "alive": sum(n.alive for n in sensors),
            "remaining_energy": round(remaining, 5),
            "spent_energy": round(sum(sum(n.spent.values()) for n in sensors), 5),
            "nodes": [{"id": n.id, "energy": round(n.energy, 5),
                       "predicted": round(max(0.0, n.energy - n.drain * self.c.horizon), 5),
                       "drain": round(n.drain, 5), "alive": n.alive,
                       "parent": n.parent if n.alive else None, "queue": len(n.queue)}
                      for n in self.nodes]})

    def step(self):
        c = self.c
        self.receive_inbox()
        self.evaluate_forecasts()
        if c.scenario == "failure" and self.t == c.duration // 2:
            n = self.nodes[1]
            if n.alive:
                n.alive = False
                n.death = self.t
                n.failure = "injected"
                self.log("injected_failure", node=1)
        if self.t and self.t % c.decide_every == 0:
            self.update_predictor()
        for n in self.nodes[1:]:
            if n.alive:
                self.spend(n, c.idle_cost, "idle")
        if self.t % c.advertise_every == 0:
            self.advertise()
        if self.t % c.decide_every == 0:
            for n in self.nodes[1:]:
                if n.alive:
                    self.choose_parent(n)
        self.generate()
        self.forward()
        self.t += 1

    def run(self):
        self.snapshot()
        while self.t < self.c.duration:
            self.step()
            if self.t % 5 == 0:
                self.snapshot()
        self.receive_inbox()  # last-slot arrivals at t = duration
        # Evaluate any forecasts exactly due at the end (including non-5 horizons).
        self.evaluate_forecasts()
        # Finalize OFFLINE queues, without draining a healthy queue past the horizon.
        for n in self.nodes[1:]:
            if not n.alive:
                self.drops["node_offline"] += len(n.queue)
                n.queue.clear()
        if self.snapshots[-1]["time"] == self.t:
            self.snapshots.pop()
        self.snapshot()
        sensors = self.nodes[1:]
        spent = sum(sum(n.spent.values()) for n in sensors)
        pending = sum(len(n.queue) for n in sensors) + len(self.inbox)
        battery_deaths = [n.death for n in sensors if n.failure == "battery"]
        metrics = {
            "algorithm": self.algorithm, "label": LABELS[self.algorithm],
            "offered": self.offered, "generated": self.generated,
            "source_unavailable": self.unavailable, "delivered": self.delivered,
            "dropped": sum(self.drops.values()), "pending": pending,
            "packet_delivery_ratio": self.delivered / self.generated if self.generated else 0,
            "demand_delivery_ratio": self.delivered / self.offered if self.offered else 0,
            "average_delay": statistics.mean(self.delays) if self.delays else None,
            "average_hops": statistics.mean(self.hops) if self.hops else None,
            "energy_spent": spent,
            "energy_per_delivered": spent / self.delivered if self.delivered else None,
            "alive": sum(n.alive for n in sensors),
            "first_battery_death": min(battery_deaths) if battery_deaths else None,
            "route_changes": self.route_changes, "tx_attempts": self.tx_attempts,
            "control_messages": self.control_messages, "control_receptions": self.control_receptions,
            "prediction_mae": statistics.mean(self.prediction_errors) if self.prediction_errors else None,
            "prediction_normalized_mae": statistics.mean(self.prediction_errors_normalized) if self.prediction_errors else None,
            "prediction_samples": len(self.prediction_errors),
            "drops_by_reason": dict(self.drops),
            "energy_by_category": dict(sum((n.spent for n in sensors), Counter())),
        }
        assert self.offered == self.generated + self.unavailable
        assert self.generated == self.delivered + sum(self.drops.values()) + pending
        return {"metrics": metrics, "snapshots": self.snapshots, "events": self.events}


def compare(config=None):
    c = config or Config()
    runs = {algorithm: Simulation(c, algorithm).run() for algorithm in ALGORITHMS}
    positions, links, levels, _ = make_topology(c)
    prototype = Simulation(c)
    return {"config": asdict(c), "topology": {
        "nodes": [{"id": i, "x": x, "y": y, "level": levels[i],
                   "capacity": prototype.nodes[i].capacity} for i, (x, y) in enumerate(positions)],
        "links": [{"a": a, "b": b, "quality": round(p, 5)} for a, b, p in links]},
        "runs": runs,
        "model": "Illustrative EU; fixed BFS levels; local lossy advertisements; independent links; no RF collision model."}
