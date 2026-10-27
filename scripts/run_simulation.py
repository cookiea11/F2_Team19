"""Run a saved network simulation configuration without the dashboard."""
from dataclasses import asdict
import argparse
import json
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from simulator import Config, compare

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=ROOT / "simulation/F2_Team19_Config.json")
    parser.add_argument("--out", type=Path, default=ROOT / "results/F2_Team19_Simulation.json")
    args = parser.parse_args()
    c = Config(**json.loads(args.config.read_text()))
    result = compare(c)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2))
    topology = ROOT / "simulation/F2_Team19_Topology.json"
    topology.write_text(json.dumps(result["topology"], indent=2))
    print(f"Saved {args.out} and {topology}")
    for algorithm, run in result["runs"].items():
        m = run["metrics"]
        print(f"{algorithm}: demand delivery {m['demand_delivery_ratio']:.2%}, first battery death {m['first_battery_death']}")

if __name__ == "__main__":
    main()
