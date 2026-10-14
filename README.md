# FRESH retirement planner

FRESH projects whether gross household income and Cash, RRSP and TFSA savings
cover a retirement income target. It supports one or two people, separate
retirement ages, contribution and pension indexation, annual investment returns,
and client and advisor PDF reports. All amounts are Canadian dollars (CAD).

Use the [browser planner](https://paohenr1.github.io/Fresh/) or run the Python
planner locally. Both use the same annual calculation conventions, verified by
cross-language comparisons. The browser calculates and exports PDFs on the
visitor's device; the Python interface uses a local server on this computer.

## Run the Python planner

Use Python 3.11 or newer. From the repository root on Windows:

```text
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe app.py
```

Open `http://127.0.0.1:8765/` and keep the terminal running. After setup, you can
also double-click `Start FRESH.cmd`. Edit inputs to recalculate the dashboard.
Export an advisor PDF to keep a record of all inputs and the annual projection.
Refreshing starts again from the loaded input file; edits are not saved automatically.

The example in `examples/fictional.json` is fictional and pinned to October 8,
2026. Rates are percentage numbers: `2.5` means 2.5% annually. General inflation
is separate from each contribution or pension's indexation rate. Contribution
indexation starts at t=0 in the projection's initial year; pension indexation
starts at t=0 in that person's retirement year. No immediate increase is applied.

To generate CSV, structured JSON and an HTML snapshot:

```text
.venv\Scripts\python.exe main.py examples/fictional.json --output output
```

The HTML file is a snapshot; use the local server to edit numbers. Generated
reports and private scenarios should stay in the ignored `output/` directory.
See [running and exporting](docs/usage.md) for loading scenarios, date overrides,
PDF contents and local browser development.

## Understand and verify the model

- [Inputs, formulas and assumptions](docs/model.md): percentages, benefit timing,
  annual cash-flow order, surplus saving, real values and financial limitations.
- [A fictional projection year](docs/example.md): a numerical walkthrough and
  annual balance reconciliation.
- [Code structure and development](docs/development.md): how the files connect,
  Python concepts and direct reuse of the calculation functions.
- [Verification](VERIFICATION.md): reproducible tests and numeric comparisons.
- [Source review](MODEL_REVIEW.md): original behavior, ambiguities and intentional
  extensions. No workbook was available; the original formulas are TypeScript.
- [Historical verification](docs/verification-history.md): dated evidence from
  earlier versions, clearly separated from current results.
- [Browser source guide](web/README.md): frontend setup and test prerequisites.

The engine is deterministic, annual and pre-tax. It does not model taxes,
clawbacks, account contribution limits, RRIF/LIF rules or return simulations.
The inherited 2026 CPP/OAS reference values are assumptions, not verified current
entitlements. These limitations are detailed in the model guide.

Contributions stop in each person's retirement year. Once either person retires,
net income above the household target is saved to Cash before investment growth.
Withdrawals stop at available assets and any remaining gap is recorded explicitly.
Dashboard and PDF values are nominal, rounded to whole dollars; CSV and JSON
retain full precision and include values in the initial year's purchasing power.

## Reference source

The recovered source is preserved unchanged in `original_fresh/`, pinned to
commit `a0623571bd85c0c75c284efe4ba4dee550db8d9b`. [SOURCE.json](SOURCE.json)
records its provenance and file hashes. Numeric contribution rates, optional
pension indexation and retirement-surplus saving are intentional extensions;
the verification guide explains how they are compared with the original.

The previous main application is retained on the
[backup branch](https://github.com/paohenr1/Fresh/tree/codex/backup-main-2026-10-13),
at commit `b3368e7843ae9661916cc2ba4ce7f8cde125f300`. The active browser application
is in `web/`; `original_fresh/` is a reference, not the deployed application.
