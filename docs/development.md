# Code structure and development

Run commands from the repository root.

## How the files connect

```text
main.py -> inputs.py -> projection.py -> reporting.py
                          |               |
                          +-- indexation.py
tests/ -> hand-calculated cases and original TypeScript comparison
```

- `inputs.py` defines the input records, fixed government reference assumptions,
  JSON loading, and validation.
- `indexation.py` contains compounding and purchasing-power formulas.
- `projection.py` owns benefit calculations and the annual cash-flow sequence.
- `reporting.py` turns calculation results into tables, summaries, CSV and HTML.
- `report.css` is the original FRESH stylesheet. `report_template.html` supplies
  the page layout and small display-only interactions. Both are embedded in
  the generated HTML, so the report works offline without separate assets.
- `main.py` handles files and command-line options. The model functions do not
  depend on this interface.
- `app.py` serves the editable planner on this computer. `planner.js` collects
  input changes and displays Python's response; it contains no financial formulas.
- `pdf_reporting.py` creates the client presentation and advisor scenario reports
  from the same validated inputs and projection functions.

A `dataclass` is a small Python record with named fields. It lets you see each
input or output by name instead of remembering tuple positions. `frozen=True`
prevents rebinding record fields; nested dictionaries remain mutable, so treat
completed input/results records as read-only. Type hints describe the expected
types; `validate()` performs actual runtime checks. `dict[str, float]` means a
dictionary mapping account names to numbers. `None` represents an absent spouse
or an age after a person's plan ends. `dataclasses.replace()` makes a revised
record conveniently, as demonstrated in the tests. The calculation keeps local
mutable account balances but never mutates input records.

You can reuse the engine directly:

```python
import json
from datetime import date
from pathlib import Path
from inputs import scenario_from_dict
from projection import project
from reporting import annual_table

data = json.loads(Path("examples/fictional.json").read_text())
scenario = scenario_from_dict(data)
result = project(scenario, date.fromisoformat(data["as_of"]))
table = annual_table(result, scenario)  # list of dictionaries, one per year
print(table[0]["closing_total_nominal_cad"])
```


[Back to the README](../README.md).

## Development checks

Install Python dependencies with the README setup commands. Use Node.js 24 or
newer for browser development and TypeScript reference comparisons. From the
repository root:

```text
npm ci --prefix web
npm run dev --prefix web
```

The two engines are separate implementations; changing one does not update the
other. Keep the fictional examples aligned and run the [verification commands](../VERIFICATION.md)
when formulas change. The preserved reference files must remain unchanged.
