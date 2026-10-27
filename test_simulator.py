"""Meaningful correctness checks. Run: python -m unittest -v."""
from dataclasses import replace
import json
import unittest
from simulator import ALGORITHMS, Config, Observation, Simulation, compare
from app import config_from_payload


class SimulatorTests(unittest.TestCase):
    def test_reproducible(self):
        c = Config(nodes=12, duration=80)
        self.assertEqual(compare(c), compare(c))

    def test_packet_and_energy_conservation(self):
        for scenario in ("steady", "burst", "failure"):
            for algorithm in ALGORITHMS:
                sim = Simulation(Config(nodes=15, duration=180, scenario=scenario), algorithm)
                result = sim.run()
                m = result["metrics"]
                self.assertEqual(m["offered"], m["generated"] + m["source_unavailable"])
                self.assertEqual(m["generated"], m["delivered"] + m["dropped"] + m["pending"])
                for n in sim.nodes[1:]:
                    self.assertAlmostEqual(n.capacity, n.energy + sum(n.spent.values()), places=7)
                    self.assertGreaterEqual(n.energy, 0)
                self.assertLessEqual(m["tx_attempts"], sim.c.nodes * sim.c.duration)
                self.assertTrue(all(delay >= 1 for delay in sim.delays))

    def test_all_selected_routes_are_acyclic(self):
        for algorithm in ALGORITHMS:
            sim = Simulation(Config(nodes=20, duration=180), algorithm)
            r = sim.run()
            for snapshot in r["snapshots"]:
                for n in snapshot["nodes"]:
                    parent = n["parent"]
                    if parent is not None:
                        self.assertLess(sim.nodes[parent].level, sim.nodes[n["id"]].level)

    def test_identical_offered_workload(self):
        r = compare(Config(duration=100))
        self.assertEqual(len({x["metrics"]["offered"] for x in r["runs"].values()}), 1)
        series = [[s["offered"] for s in r["snapshots"]] for r in r["runs"].values()]
        self.assertEqual(series[0], series[1])
        self.assertEqual(series[1], series[2])

    def test_prediction_changes_an_equal_battery_choice(self):
        sim = Simulation(Config())
        n = next(n for n in sim.nodes[1:] if len([j for j in sim.neighbors[n.id]
                     if 0 < sim.nodes[j].level < n.level]) >= 2)
        choices = sorted(j for j in sim.neighbors[n.id] if 0 < sim.nodes[j].level < n.level)[:2]
        a, b = choices
        n.observations = {a: Observation(80, 100, 1.0, 0, 0, True),
                          b: Observation(80, 100, 0.1, 0, 0, True)}
        sim.quality[(min(n.id, a), max(n.id, a))] = .9
        sim.quality[(min(n.id, b), max(n.id, b))] = .9
        sim.algorithm = "reactive"
        sim.choose_parent(n)
        self.assertEqual(n.parent, a)  # tie breaks by node ID
        n.parent = None
        sim.algorithm = "predictive"
        sim.choose_parent(n)
        self.assertEqual(n.parent, b)  # same battery, lower predicted drain

    def test_ewma_and_horizon(self):
        sim = Simulation(Config(nodes=10, duration=80, horizon=37))
        n = sim.nodes[1]
        n.last_energy = 30
        n.energy = 25
        n.drain = 0
        sim.t = 5
        sim.update_predictor()
        self.assertAlmostEqual(n.drain, .35)
        forecast = dict(sim.forecasts[42])[n.id]
        self.assertAlmostEqual(forecast, 25 - 37 * .35)
        result = Simulation(Config(duration=80, horizon=37)).run()
        self.assertGreater(result["metrics"]["prediction_samples"], 0)

    def test_stale_observations_rejected(self):
        sim = Simulation()
        n = sim.nodes[1]
        n.observations = {0: Observation(0, 0, 0, 0, 0, True)}
        sim.t = 21
        sim.choose_parent(n)
        self.assertIsNone(n.parent)

    def test_hysteresis_retains_nearly_equal_route(self):
        sim = Simulation()
        n = next(n for n in sim.nodes[1:] if len([j for j in sim.neighbors[n.id]
                     if 0 < sim.nodes[j].level < n.level]) >= 2)
        a, b = sorted(j for j in sim.neighbors[n.id] if 0 < sim.nodes[j].level < n.level)[:2]
        n.observations = {a: Observation(80, 100, 0, 0, 0, True),
                          b: Observation(80, 100, 0, 0, 0, True)}
        n.parent = b
        sim.choose_parent(n)
        self.assertEqual(n.parent, b)

    def test_invalid_api_config(self):
        for payload in ({"nodes": 2}, {"nodes": "30"}, {"alpha": 0}, {"traffic": float("nan")},
                        {"duration": 20}, {"scenario": "unknown"}, {"horizon": 401},
                        {"nodes": True}, {"tx_cost": 0}):
            with self.assertRaises(ValueError):
                config_from_payload(payload)

    def test_serializable_without_nonfinite_numbers(self):
        result = compare(Config(duration=80))
        json.dumps(result, allow_nan=False)


if __name__ == "__main__":
    unittest.main()
