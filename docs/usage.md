# Using FRESH and exporting results

## Use the browser planner

Open the [browser planner](https://paohenr1.github.io/Fresh/). Use You/Spouse to
edit each person's inputs and Include spouse to change household composition.
Valid input changes recalculate the graphs, summary and annual table. Invalid or
incomplete inputs hide outdated results and disable PDF export until corrected.
Reset example restores the example inputs.

Rates are percentage numbers: `2.5` means 2.5% annually, and `0` means no annual
increase. Contribution and pension indexation are independent of general
inflation. Expand Edit indexation to change a rate; collapsing the control does
not change its value. See the [model guide](model.md) for timing and input units.
The example values are fictional, not recommendations.

### Scenarios and projection dates

Each visitor starts with a separate, unsaved scenario. Refreshing discards edits;
sharing the website link does not include them. Export a PDF to share a completed
scenario. The advisor PDF includes all inputs as well as results.

The example's projection start is fixed at October 8, 2026. Reopening the planner
does not advance that date. Current age and the initial year follow the stored
scenario date, not the computer's date. Edit date controls retain exact birth
and plan-end dates. The projection date is not an editable dashboard field and
is not printed in the PDFs; their export timestamps are not the projection date.
Use the local scenario workflow below to set a different starting date.

## Read the dashboard

| Metric | Meaning |
|---|---|
| Current savings | Combined opening Cash, RRSP and TFSA balances, before projected contributions, withdrawals or growth |
| Savings at retirement | Opening household savings in the first retirement year, before that year's cash flows and growth |
| Balance at plan end | Total savings after growth in the final projection year |
| Years covered | Number of fully funded retirement years; later funded years do not erase an earlier shortage |
| Annual income target | Gross target in the initial retirement year; later targets follow general inflation |

For already-retired households, Savings at projection start replaces the
retirement-balance label; the planner does not reconstruct past balances.
Individual retirement and plan-end cards show ages attained in those years;
household cards show calendar years. On narrow screens, the summary strip
scrolls horizontally.

Dashboard tables and PDFs display nominal CAD rounded to whole dollars. CSV and
JSON retain full precision and also include values in the starting year's
purchasing power. Working employment income counts toward funding during
partial retirement but is excluded from the income chart. Consult the
[model assumptions](model.md) when interpreting the charts and funding gaps.

## Export PDFs

| Export | Contents |
|---|---|
| Client PDF | Summary metrics, scenario overview, both graphs and the compact annual projection table |
| Advisor PDF | The same dashboard and annual table, plus every person-specific input and shared assumption, including collapsed indexation inputs |

Both exports use the latest valid scenario and include all projection years.
They do not include separate account-reconciliation tables. While calculations
are updating or inputs are invalid, export is disabled. Inputs are briefly
locked during export to keep the downloaded record consistent.

PDF dates are labelled, and export timestamps use UTC. Both reports display
Current age and Age at plan end. Keep the scenario's projection date with any
PDF used as a record, because the export timestamp alone does not identify it.

## Run the local Python planner

Run commands from the repository root. Use Python 3.11 or newer. The calculation
engine and CSV/JSON exports use the standard library; PDF export requires
ReportLab from `requirements.txt`.

On Windows, create the environment and install dependencies once:

```text
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe app.py
```

Open `http://127.0.0.1:8765/` and keep the terminal running. After setup, you can
also double-click `Start FRESH.cmd`; the launcher uses `.venv` when it exists.
On Windows, `py -3` can replace `python` when creating the environment. Quote
paths containing spaces.

The local dashboard is editable. Refreshing returns to the loaded file, so edits
are not saved automatically. Reset example restores the loaded inputs. Export
an advisor PDF to retain edited inputs and results.

### Load a scenario or change its date

Copy `examples/fictional.json` into the ignored `output/` directory and edit its
fields, including `as_of` to set the projection date. Update incomes, balances
and contributions to the intended starting date as well. The [model guide](model.md)
describes the input fields and validation rules.

Load a scenario with:

```text
.venv\Scripts\python.exe app.py output/my-scenario.json
```

A saved `projection.json` generated by the command-line interface can also be
reopened this way. Changing the projection date changes the income and
contribution base year; it is not simply a display setting.

### Generate CSV, JSON and HTML

```text
.venv\Scripts\python.exe main.py examples/fictional.json --output output
.venv\Scripts\python.exe main.py examples/fictional.json --as-of 2028-10-08 --output output/2028
```

The second command demonstrates a deliberate date override; use appropriately
updated inputs for a real scenario. The date does not change automatically.

| File | Contents |
|---|---|
| `annual.csv` | Full annual table, including household and account reconciliation fields |
| `projection.json` | Effective inputs, summary metrics and unrounded annual results |
| `report.html` | Standalone, offline snapshot with saved inputs, summary metrics, graphs and an expandable nominal annual table |

The HTML report is a snapshot, not an editable planner. Hover over a graph for
annual values, or focus it and use the arrow keys. Use `app.py` to change inputs
interactively. CSV and JSON are command-line exports, not dashboard buttons.
Keep private scenarios and generated files in ignored `output/` directories.

## Privacy and sharing

Browser calculations and PDF generation run on the visitor's device. After the
page loads, calculations and PDF downloads work without a network connection.
Financial inputs are not sent to a calculation server or stored remotely. The
static site host may record ordinary page and asset requests.

The local Python planner serves the interface on the local computer and does
not send financial inputs to an external service. File exports deliberately
save inputs and results to disk; downloaded PDFs also contain scenario details.
Check their contents before sharing them. Example records are fictional.

## Developer references

See [code structure and development](development.md) for the Python engine,
[browser development](../web/README.md) for frontend commands, and
[verification](../VERIFICATION.md) for cross-language and interface checks.
Historical implementations are described separately in
[source provenance](provenance.md).

[Back to the README](../README.md).
