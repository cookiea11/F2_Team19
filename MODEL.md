# Exact model and algorithm

## 1. Scope

This is a custom, discrete-time, slotted sensor-to-gateway routing simulator.
There are N battery-powered sensors plus gateway 0. Coordinates and radio radius
are abstract spatial units. Time advances in one-second slots. Positions do not move.
Physical links are undirected; selected forwarding edges point toward the gateway.

Initial BFS levels are computed centrally from the connected physical graph and
remain fixed. Each sensor may forward only to a neighbor with a strictly smaller
level. In this unweighted graph such candidates lie one BFS level closer to the root.
This restricts all strategies to minimum-hop paths on the initial graph. Their
difference is which eligible parent they select, not a search over arbitrary paths.
The level is not the full RPL Rank. This is an RPL-inspired constraint, not RPL.

Dead nodes are not removed from levels. A surviving path that requires moving
sideways or upward in this initial scaffold cannot be used. There is no distributed
level repair, downward routing, or general peer-to-peer route discovery in this version.

## 2. Traffic and links

Each sensor has one scheduled-reading Bernoulli trial per slot, with probability
0.03 by default. A burst triples it during the middle third of the experiment.
The same scheduled readings exist for every strategy, even when a source has died.
An offline source contributes to source_unavailable rather than generated packets.

Neighbors lie within radius 32. Each link has a fixed success probability derived
from distance, with a small seeded perturbation. This probability is also provided
as the routing link-quality estimate: online link-quality learning is not implemented.

A node can attempt at most one queued packet per slot. Successful packets reach
the neighbor at the next slot boundary, preventing instant multi-hop delivery.
Failures retry up to three attempts per hop on the current link. A parent change
resets the head packet's attempt counter; the network TTL still bounds its lifetime.
Packets queue until a route exists or their 100-second TTL expires. Queues hold
20 packets. Failed transmission attempts still consume transmit energy; powered
receivers consume receive energy even when the link delivery fails.

Links are independent. Simultaneous transmissions do not interfere. There is no
CSMA/CA, RF collision, hidden-terminal, capture, propagation-delay, or bit-level
model. A one-second hop duration is an illustrative simulation service slot, not
a measured IEEE 802.15.4 radio delay. Source iteration order is deterministic;
it can influence energy exhaustion within a slot. This is a stated approximation.

## 3. Energy accounting

Default costs, all in illustrative energy units (EU):

| Operation | Cost |
| --- | ---: |
| Data transmission attempt | 0.10 |
| Data reception attempt | 0.05 |
| Idle slot | 0.005 |
| Control broadcast | 0.02 |
| Control reception attempt | 0.005 |

Ordinary sensor initial capacities are seeded between 85 and 115 EU. Sensor 1 has
38 EU, representing a deliberately smaller battery. Each node starts fully charged
relative to its own capacity. Gateway 0 is externally powered and is excluded from
battery totals. Sensor energy cannot become negative. Death occurs at zero energy.

The failure scenario forcibly takes sensor 1 offline halfway through the run if
it is still alive. Its unused battery is retained in the physical remaining-energy
total, and is not counted as consumed. Forced offline status is not a battery death.

No joule, mAh, or real-world lifetime claims can be made without calibrating this
model against a device and radio power profile. Duty cycling and battery voltage
curves are not modeled. Energy spent includes all modeled sensor control traffic.

## 4. Local advertisements and available information

Every ten seconds, every live node broadcasts a status record:

```
sender_id, timestamp, remaining_energy, capacity,
smoothed_drain, queue_length, alive
```

These are simulator objects rather than serialized wire packets. Each listener pays
receive energy; successful reception is sampled using link quality. An observation
older than 20 seconds expires. Dead nodes stop broadcasting; the protocol discovers
this through stale observations and unsuccessful forwarding, not a global battery oracle.

Routing logic reads neighbors' received observations. The simulator as a whole
maintains global ground truth for execution and visualization. The initial BFS
scaffold and the provided link-quality estimates are global setup assumptions.
Control-message sizes are not modeled in bytes; their energy cost is fixed per event.
All three algorithms use this same monitoring schedule for a controlled comparison.
This is not a comparison against a separately optimized low-overhead shortest-path stack.

## 5. Predictor

Every five seconds, node i measures its own recent energy drain:

```
r_i = (previous_sample_energy - current_energy) / 5
d_i = alpha * r_i + (1 - alpha) * previous_d_i
alpha = 0.35, initial d_i = 0
```

For an advertisement received by a node at time t, let its timestamp be t_a.
PAMR predicts the neighbor's remaining energy at t + H:

```
predicted_energy = max(0, advertised_energy - advertised_drain * (H + t - t_a))
H = 40 seconds by default
```

The age correction accounts for energy spent since the advertisement. The reactive
baseline simply uses the last advertised remaining energy without forecasting.
The local inspector forecast uses each node's current energy and drain, so it need
not equal an older estimate held by a neighbor.

This is a lightweight statistical forecast, not a trained neural network. It assumes
recent drain is useful over the short horizon. Abrupt load changes can violate that
assumption; adapting the route also changes the future energy trajectory.

## 6. Parent selection

Eligible parents have a lower initial BFS level and a fresh live advertisement.
The gateway has cost 0 and is always preferred when directly eligible.

For each other candidate j:

```
energy_risk = 1 - min(1, predicted_energy_j / capacity_j)
link_loss = 1 - link_success_probability(i, j)
queue_fraction = min(1, advertised_queue_j / 20)

cost = 0.65 * energy_risk + 0.20 * link_loss + 0.15 * queue_fraction
```

All terms are normalized to [0,1]. Higher energy is better; higher loss or queue is
worse. These weights prioritize energy while retaining reliability and congestion
considerations. They are design settings, not learned or proven optimal weights.
No separate hop term is necessary here: eligibility already enforces progress along
the initial shortest-hop scaffold. There is no hard 20% battery exclusion threshold.

Every five seconds, choose the minimum-cost eligible parent. Retain a valid current
parent unless the candidate improves cost by more than 0.06. This absolute score
margin is hysteresis; it is not a percentage of the old score. Invalid current
parents can be replaced without satisfying the margin.

Baselines:

- **Shortest-hop:** use lower-level candidates; break ties with higher link quality,
  then lower node ID. Advertisements are still used for availability.
- **Reactive:** use the same weighted cost with advertised current energy.
- **PAMR:** use the same cost with age-corrected future energy.

We adapt the selected parent, not the weights or radio power. A single valid parent
is active per sensor at a time; alternate physical mesh paths remain available.

## 7. Metrics

| Metric | Definition |
| --- | --- |
| Offered | All scheduled sensor readings, including offline sources |
| Generated | Offered readings whose source is alive when scheduled |
| Source unavailable | Offered readings at offline sources |
| Delivered | Generated packets received by gateway by the observation horizon |
| Dropped | Generated packets lost to a modeled terminal drop condition |
| Pending | Generated packets still queued or in flight at the end |
| Packet delivery ratio | delivered / generated |
| Demand delivery ratio | delivered / offered; includes source availability impact |
| Average delay | Mean arrival time minus creation time over delivered packets only |
| Energy per delivered | Total sensor energy spent / delivered packets |
| First battery death | Earliest depletion time, excluding injected failures |
| Route changes | Parent changes after an initial assignment, including parent loss |
| Prediction MAE | Mean absolute forecast error in EU over matured forecasts |

Conservation checks: offered = generated + source_unavailable; generated = delivered
+ dropped + pending. Each sensor's capacity = remaining energy + accounted consumption.

A run with no battery death is right-censored at its duration: it does not demonstrate
infinite lifetime. We report a count of runs with observed deaths rather than an
incorrect mean that silently ignores censored runs. Long delay may reflect congestion;
low mean delay can also reflect loss of slow packets, so inspect delivery jointly.
Packets pending at the end are not silently reclassified as drops or delivered later.

Forecasts are made every five seconds after warm-up and checked H seconds later,
including horizons that are not multiples of five. Forecasts spanning an injected
failure are excluded. Errors describe the actual adaptive run, whose routes can
change after a forecast. They do not establish counterfactual forecast accuracy.

## 8. Reproducibility and fairness

Topology, capacities, scheduled traffic, and per-link qualities depend only on the
seed and configuration. Random draws are deterministic hashes of event identifiers,
so a different route cannot consume a random draw and perturb future offered traffic.
Actual successful deliveries differ when strategy decisions change links or times.

All algorithms share duration, topology, energy costs, queue limits, and control
schedule. Compare matched seeds 0-9 separately for each scenario. The supplied submission suite uses five cases: low, medium, and high steady loads, a burst, and a relay failure (150 runs in total). Report means and
sample standard deviations; the supplied experiment does not perform a significance
test. Avoid choosing one favorable seed and claiming a universal improvement.

## 9. Complexity

At a routing decision, a node scans d eligible neighbors: O(d) time, O(d) stored
observations. The EWMA update and scalar forecast cost O(1) per node. Network-wide
simulation topology construction is O(N²); that is not a per-node protocol requirement.
Visualization and history storage are simulator overhead, not embedded-node overhead.

## Sources for background

- IETF RFC 6550, RPL: https://www.rfc-editor.org/rfc/rfc6550.html
- NIST, single exponential smoothing: https://www.itl.nist.gov/div898/handbook/pmc/section4/pmc431.htm

These sources explain background concepts. They do not endorse or validate this
custom weighted algorithm, parameter settings, or simulator.
