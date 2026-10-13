"""Run the fictional example or a scenario JSON without an application interface."""

import argparse
from datetime import date
import json
from pathlib import Path

from inputs import scenario_from_dict
from projection import project
from reporting import annual_table, summary, write_csv, write_html


def main() -> None:
    """Read explicit inputs, calculate once, and write reusable reports."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("inputs", nargs="?", type=Path,
                        default=Path(__file__).parent / "examples" / "fictional.json")
    parser.add_argument("--as-of", type=date.fromisoformat, help="Override the JSON as_of date (YYYY-MM-DD)")
    parser.add_argument("--output", type=Path, default=Path("output"))
    args = parser.parse_args()
    try:
        data = json.loads(args.inputs.read_text(encoding="utf-8"))
        scenario = scenario_from_dict(data)
        as_of = args.as_of or date.fromisoformat(data["as_of"])
        projection = project(scenario, as_of)
        records = annual_table(projection, scenario)
        results = summary(projection, scenario)
        args.output.mkdir(parents=True, exist_ok=True)
        write_csv(records, args.output / "annual.csv")
        effective_inputs = {**data, "as_of": as_of.isoformat()}
        payload = {"as_of": as_of.isoformat(), "inputs": effective_inputs,
                   "summary": results, "annual_table": records}
        (args.output / "projection.json").write_text(
            json.dumps(payload, indent=2, allow_nan=False), encoding="utf-8")
        write_html(projection, scenario, args.output / "report.html")
        print(json.dumps(results, indent=2, allow_nan=False))
        print(f"Reports: {args.output.resolve()}")
    except (OSError, ValueError, KeyError, OverflowError) as error:
        parser.exit(2, f"FRESH: {error}\n")


if __name__ == "__main__":
    main()
