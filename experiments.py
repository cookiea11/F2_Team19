"""Repeat all strategies on matched seeds and export actual results."""
import argparse
import csv
import json
from pathlib import Path
import statistics
from simulator import Config, compare

CASES = {
    "low_load": ("steady", 0.015),
    "medium_load": ("steady", 0.03),
    "high_load": ("steady", 0.06),
    "burst": ("burst", 0.03),
    "failure": ("failure", 0.03),
}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds", type=int, default=10)
    parser.add_argument("--out", default="results")
    parser.add_argument("--scenario", choices=["all", "steady", *CASES], default="all")
    args = parser.parse_args()
    if not 1 <= args.seeds <= 100:
        parser.error("--seeds must be between 1 and 100")
    output = Path(args.out)
    output.mkdir(parents=True, exist_ok=True)
    scenarios = list(CASES) if args.scenario == "all" else ["medium_load" if args.scenario == "steady" else args.scenario]
    rows = []
    for scenario in scenarios:
        mode, traffic = CASES[scenario]
        for seed in range(args.seeds):
            data = compare(Config(seed=seed, scenario=mode, traffic=traffic))
            for run in data["runs"].values():
                row = {"scenario": scenario, "traffic": traffic, "duration": 400, "seed": seed, **run["metrics"]}
                rows.append({k: v for k, v in row.items() if not isinstance(v, dict)})
        print(f"Completed {scenario}: {args.seeds} matched seeds", flush=True)
    with (output / "experiments.csv").open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    summary = []
    metrics = ["demand_delivery_ratio", "packet_delivery_ratio", "average_delay",
               "energy_per_delivered", "route_changes", "prediction_mae"]
    for scenario in scenarios:
        for algorithm in data["runs"]:
            group = [r for r in rows if r["scenario"] == scenario and r["algorithm"] == algorithm]
            item = {"scenario": scenario, "traffic": CASES[scenario][1], "algorithm": algorithm, "runs": len(group)}
            for metric in metrics:
                values = [r[metric] for r in group if r[metric] is not None]
                item[metric + "_mean"] = statistics.mean(values) if values else None
                item[metric + "_sd"] = statistics.stdev(values) if len(values) > 1 else None
            # A missing death is right-censored: don't replace it with zero or
            # average only runs with observed deaths and call that mean lifetime.
            deaths = [r["first_battery_death"] for r in group if r["first_battery_death"] is not None]
            item["runs_with_battery_death"] = len(deaths)
            item["runs_without_battery_death_within_400s"] = len(group) - len(deaths)
            summary.append(item)
    (output / "summary.json").write_text(json.dumps(summary, indent=2))
    print(f"Saved {output / 'experiments.csv'} and {output / 'summary.json'}")


if __name__ == "__main__":
    main()
