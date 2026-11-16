# FRESH retirement planner

FRESH is a Canadian retirement scenario calculator for individuals and couples.
It projects whether gross household income and Cash, RRSP and TFSA savings cover
an income target through the planning horizon. All amounts are Canadian dollars
(CAD).

## Try the planner

Open the [browser planner](https://paohenr1.github.io/Fresh/), edit the fictional
example, and explore the projected balances, income and annual funding gaps.
You can set separate retirement ages, contributions, pensions, benefit start
ages, indexation rates and investment returns, then export a client or advisor
PDF.

Calculations and PDF generation run on your device. Scenarios are not saved
automatically: refreshing resets your edits, and sharing the website link does
not share your scenario. Export an advisor PDF to retain all inputs and results.
The example starts on October 8, 2026; its projection date does not advance
automatically. See [using the planner and exporting results](docs/usage.md) for
details, including setting the projection date in a local scenario.

## Scope and limitations

FRESH provides deterministic, annual, pre-tax illustrations, not a comprehensive
retirement plan. It uses fixed annual return assumptions and an
inflation-adjusted target based on 100% of entered gross income.

It does not calculate taxes, OAS clawback, GIS, contribution limits, RRIF/LIF
rules, fees, legal account transfers, survivor entitlements or return
simulations. RRSP and TFSA balances do not represent equal after-tax spending
power. The 2026 CPP/OAS reference amounts are model assumptions, not verified
current entitlements. Values are estimates, not guarantees.

Read the [model assumptions](docs/model.md) before interpreting results. A
[worked fictional year](docs/example.md) shows how contributions, income,
withdrawals and investment growth reconcile.

## Run locally with Python

The local planner provides an editable dashboard and PDF reports. The
command-line interface also exports CSV, JSON and a standalone HTML snapshot.
The Python and browser engines use the same annual calculation conventions;
[verification](VERIFICATION.md) documents their comparison tests and limits.

Use Python 3.11 or newer. From the repository root on Windows:

```text
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe app.py
```

Open `http://127.0.0.1:8765/` and keep the terminal running. After setup, you can
also double-click `Start FRESH.cmd`. Edits are not saved automatically.

To generate file exports:

```text
.venv\Scripts\python.exe main.py examples/fictional.json --output output
```

Keep private scenarios and generated reports in the ignored `output/` directory.
See the [usage guide](docs/usage.md) for scenario loading, date overrides and
export contents.

## Documentation

| Guide | Contents |
|---|---|
| [Using FRESH](docs/usage.md) | Browser and local setup, dashboard metrics, exports and privacy |
| [Model assumptions](docs/model.md) | Input units, formulas, annual timing and financial limitations |
| [Worked example](docs/example.md) | A fictional projection year and balance reconciliation |
| [Verification](VERIFICATION.md) | Reproducible checks, recorded results and their limits |
| [Development](docs/development.md) | Code structure and direct reuse of the Python engine |
| [Browser development](web/README.md) | Frontend setup, tests and publishing |

## Source provenance

The active browser application is in `web/`. The immutable `original_fresh/`
directory is a historical comparison fixture, not the deployed application or
current setup guide. See [source provenance](docs/provenance.md) for the pinned
reference, implementation differences and historical verification records.
