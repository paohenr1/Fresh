# FRESH — browser and Python planners

This is the main version of [paohenr1/Fresh](https://github.com/paohenr1/Fresh).
The previous browser application is preserved on the
[codex/backup-main-2026-10-13 branch](https://github.com/paohenr1/Fresh/tree/codex/backup-main-2026-10-13),
at commit `b3368e7843ae9661916cc2ba4ce7f8cde125f300`.
The older recovered source used for numerical parity remains in `original_fresh/`.

The updated browser planner in `web/` publishes to
[the shareable GitHub Pages dashboard](https://paohenr1.github.io/Fresh/).
It runs calculations and both PDF exports on the visitor's device, without
a Python server or hosting account. The Python planner continues to run locally
with `app.py`, using the same formulas and example inputs.
The Python verification workflow checks calculations, PDF routes and source parity.

This project reproduces the recovered FRESH calculation engine, with numeric
annual indexation rates replacing the flat/inflation contribution switches.
It also supports the approved extension of a separate annual pension indexation
rate per person; 0% preserves the original fixed pension.
It projects whether gross income and savings cover a gross retirement income
target. Dollar amounts are CAD. Values are estimates, not guarantees.

The [source review](MODEL_REVIEW.md) documents the original calculations,
ambiguities, intentional changes and possible future improvements. Original
source and specification are in `original_fresh/`, pinned to commit
`a0623571bd85c0c75c284efe4ba4dee550db8d9b`. No workbook was found: this model's
formulas were implemented in TypeScript.

## Run the fictional example

For the **editable planner**, run `python app.py` in this folder (or double-click
`Start FRESH.cmd` on Windows), then open `http://127.0.0.1:8765`. Keep the terminal
open while using the planner. Change any input to recalculate the graphs,
summary and annual table through Python. Contribution increases are editable
percentages: 0 means flat; 2.5 means 2.5% annually. The example's different rates
are fictional demonstration inputs, not recommendations.

Use You/Spouse to edit each person, Include spouse to change household composition,
and Reset example to restore the loaded inputs. Export the advisor PDF to keep
a record of your edited inputs and results. Reopening or refreshing starts with
the file originally loaded. CSV and JSON buttons are omitted from the dashboard;
`python main.py` still generates those files. Previously saved scenario JSON can
be reopened with `python app.py path/to/projection.json`.
Invalid or incomplete inputs hide outdated results and disable PDF exports until
corrected. The starting date remains stored as `as_of` in the scenario file and
does not advance automatically; it is no longer shown as a dashboard/PDF field.

`output/report.html` remains an exported snapshot. Use the local planner address
above when you want to change numbers. `python main.py` generates file exports.

Use Python 3.11 or newer. The calculation engine and CSV/JSON exports use the
standard library. PDF export uses ReportLab, listed in `requirements.txt`.
On a new installation, set up the project environment once:

```text
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Then double-click `Start FRESH.cmd`, or run `.venv\Scripts\python.exe app.py`.
The launcher uses this environment when it exists. Keep the terminal open and
open the address it prints in your browser.

The dashboard now starts with **Current savings**, the combined starting Cash,
RRSP and TFSA balances for the people included in the scenario. It is the value
before projected contributions, withdrawals and investment growth.

The summary uses five white boxes with blue values in one horizontal row. Labels
are shared by the dashboard and both PDF exports: Current savings, Savings at
retirement, Balance at plan end, Years covered, and Annual income target. For an
initial-balance card, Current savings shows the projection's starting year, such
as Current savings · 2026. This follows the selected projection date, not the
computer's current calendar year. For an
individual plan the retirement/end cards show ages attained in those years; for
a household they show years to avoid mixing people's ages. Already-retired plans
retain the accurate Savings at projection start label. The annual income target
is the initial retirement-year amount; later targets follow general inflation.
On narrow screens the summary strip scrolls horizontally. Exported JSON keys
remain stable for existing users of the data.

Two buttons download PDFs from the editable planner:

- **Export client PDF:** the five summary cards, scenario overview, both area
  graphs and the original compact nominal annual projection.
- **Export advisor PDF:** the same dashboard, every client/spouse input and shared
  assumption, both graphs, and the same compact year-by-year table shown on the
  dashboard. It follows the table's selected nominal/today's CAD setting.
  Collapsed inputs and all projection years are included automatically; additional
  audit and account reconciliation tables are omitted.
  The dashboard and both PDFs consistently display Current age and Age at plan end.
  Current age uses the scenario's stored starting date. The dashboard's Edit date
  controls retain exact birth/end dates for accurate benefit timing. Neither PDF
  displays the projection date; each retains its export timestamp.

Both export the latest valid scenario. While calculations are updating or inputs
are invalid, PDF exports are disabled. Inputs are briefly locked during export
to keep the screen and downloaded record consistent. Dates are labelled explicitly;
export timestamps are in UTC. Summary cards use whole-dollar display rounding;
annual tables use the dashboard's whole-dollar display, while CSV/JSON retain
full precision. Exports
are generated locally without writing client inputs to the project folder.

From this project folder, in PowerShell or another terminal:

```text
python main.py
python main.py examples/fictional.json --output output
python main.py examples/fictional.json --as-of 2028-10-08 --output output_2028
python -m unittest discover -v
```

On Windows, `py -3` can replace `python` if that is how your interpreter is
installed. Paths containing spaces must be quoted. The default example is pinned
to October 8, 2026; a later run does not silently change the projection date.
Use `--as-of` to deliberately change it. Changing this date changes the income
and contribution base year, so use appropriately updated inputs too.

Files generated in the selected output directory:

- `annual.csv`: complete annual table with household and account reconciliation
  fields; useful in Excel without needing Excel for calculation.
- `projection.json`: effective inputs, summary metrics, and structured annual
  table; unrounded numeric values for programmatic reuse.
- `report.html`: standalone report using the original FRESH stylesheet and
  two-column layout, summary metrics, and continuous stacked area graphs.
  Hover over a graph for annual values (or focus it and use the arrow keys).
  The sidebar shows saved inputs; the You/Spouse buttons switch whose inputs
  are displayed. Expand the annual table and select nominal or today's CAD.
  Like the original website, displayed amounts round to whole dollars; CSV
  and JSON files generated by `main.py` retain full precision and all audit fields.
  The standalone report is a snapshot; use `app.py` for
  editable inputs and the two PDF buttons.

The local Python program runs without sending financial inputs anywhere.
Reports save the scenario and its results to disk; this deliberate local export
differs from the original website's unsaved browser session. Example records are
fictional and are not client information.

## Sharing the browser planner

Share https://paohenr1.github.io/Fresh/ to give someone a fresh, editable planner.
Each visitor has a separate, unsaved scenario. Sharing the link does not include
your edits; export a PDF to share your completed scenario. After the page loads,
calculations and PDF downloads work without a network connection. The static
site host may record ordinary page/asset requests, but financial inputs are not
sent to a calculation server or stored remotely.

For local browser development, run `npm ci --prefix web`, then
`npm run dev --prefix web`. Build with `npm run build --prefix web`.
`web/src/model.ts` is the browser calculation engine, `App.tsx` contains inputs
and dashboard controls, `Charts.tsx` draws area graphs and annual tables, and
`pdf.ts` generates client/advisor reports. `web/src/example.json` matches the
Python example, including its stored scenario start date; reopening the planner
does not advance that date or change birthdays automatically.

The browser and Python engines use identical annual cash-flow timing, independent
contribution/pension indexation percentages, and separate general inflation.
`python tests/verify_browser.py` compares 33 scenarios, including every annual
account reconciliation field. Results are recorded in
`browser_verification_results.json`; maximum observed difference is below
0.000000001 CAD. Browser whole-dollar display uses Python's ties-to-even rounding.
Reports use the same labels and figures; Python uses vector PDF graphs while
browser PDFs embed high-resolution images of the displayed graphs.

The Pages workflow runs calculation comparisons, model tests, browser interaction
tests and both PDF downloads before publishing `web/dist/`. The old browser
version stays on the backup branch. `original_fresh/` remains untouched for
original-source verification. Render hosting preparation was retained in the
ignored local `backups/` folder and is not needed or published.

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

## Where to change inputs

Copy `examples/fictional.json` and edit its fields. `spouse: null` selects a
single-person scenario. Dates use `YYYY-MM-DD`. Each person's accounts must
contain Cash, RRSP and TFSA. The withdrawal order must list each exactly once.
Unknown JSON fields are rejected so misspelled or unsupported assumptions do
not get silently ignored. Supply all displayed person fields; account indexation
defaults to 0 if omitted in a programmatically created Account or JSON account.

`income` means original current gross annual income. It sets a 100% income
replacement target, beginning with the first household retirement year. It is
not a separately specified after-tax spending budget. `pension` means the
expected nominal annual pension payable at that person's retirement.
`pension_indexation_percent` sets its annual increase and defaults to 0 (flat),
including when omitted from older JSON inputs. Balances and contributions are
nominal dollars at the projection base.

**All rate fields use percentage numbers:** `2.5` means 2.5%, `0` means 0%,
`6` means 6%. Python converts a rate to a fractional multiplier by dividing by
100. `0.025` means 0.025%, not 2.5%. CPP/OAS percent fields specify percent of
the reference maximum, e.g. 80 means 80%.

Each account's `indexation_percent` controls its annual **contribution**, not its
balance, pension or government benefits:

```text
contribution in year t = initial contribution × (1 + indexation_percent/100)^t
today's dollars       = nominal dollars / (1 + inflation_percent/100)^t
t                     = projection year − starting year
```

The first year is t=0, so contributions are not increased immediately. To
reproduce the original options, set rate to 0 for Flat or to general inflation
for Indexed. General inflation still controls the income target, employment
income, reference government benefits and purchasing-power conversion.
Independent contribution rates do not alter those other calculations.

Pension indexation is an intentional extension to the original fixed pensions:
`pension in year = pension at retirement × (1 + pension_indexation_percent/100)^(year − retirement_year)`.
The retirement year is t=0, with no immediate increase. For someone already
retired at projection start, elapsed years since retirement are included: enter
the retirement-year pension, rather than today's payment. Pension payments still
stop after that person's plan-end year; no survivor pension is added.

In the dashboard, each contribution and pension has a small **Edit indexation**
control, matching **Edit date**. Its percentage input is collapsed initially.
Nonzero rates appear beside the collapsed label. Opening or closing the control
does not change its value or the calculations. All rates remain listed in the
advisor PDF. General inflation remains separate from each item's rate.

Rates below -100% are invalid; -100% gives the initial contribution in year 0
and zero thereafter. The same limits apply to pension rates. Other finite indexation rates, including rates above
100%, work if the result fits floating-point capacity. Returns retain the
source range -100% to 100%; inflation retains -99% to 100%. Benefits and dates
retain source limits. A plan-end year must follow that person's retirement year.
Already retired people are supported. Loss returns never make balances negative.

## Annual order and financial assumptions

1. Record opening household balances; transfer an ended person's savings to
   the active spouse, retaining account categories.
2. Add beginning-of-year contributions for people not yet retired. No contribution
   occurs in their retirement year.
3. Compute the target and income. During partial retirement the active working
   spouse's employment income counts toward the household target.
4. Withdraw the positive income gap in the selected type order. Draw each type
   proportionally from its owners; stop at available assets and record unmet need.
5. Apply each owner's annual return to remaining balances; record closing balances.

Income is treated as annual funding available before the investment draw, even
though first benefit payments may start during the year. It is not modeled as
dated bank transactions. Retirement starts January 1 of the calendar year the
person attains the selected age. Current year and final plan year are full years.
Actual plan-end month/day has no financial effect. Age columns show age attained
in the year; ages are absent after a person's plan ends.

The amount at first retirement is **opening** savings before contributions,
withdrawals and returns, including any working spouse's contributions. For an
already retired household it is current savings, not a reconstructed historical
amount. Final savings are after final-year growth. Funded years count **all**
retirement years with zero displayed shortage; first shortage remains recorded
even if subsequent benefit income restores coverage.

Reference CPP = CAD 18,092, OAS = CAD 8,908, base year = 2026, as supplied in
FRESH. These constants are inherited assumptions, not current-rate verification.
To update them deliberately, change `GOVERNMENT` in `inputs.py` together and
reverify results. No rates are fetched at runtime.

```text
CPP = maximum × cpp_percent/100 × adjustment
      × (1 + inflation/100)^(year − reference_year) × birthday_fraction
CPP adjustment = 1 − 0.006 × months early, or 1 + 0.007 × months late
                 bounded to [0.64, 1.42], relative to age 65
OAS adjustment = 1 + 0.006 × 12 × deferral years
birthday_fraction = days from start birthday through December 31, inclusive
                    / calendar days in that year
```

February 29 becomes February 28 in non-leap benefit start years. Benefits can
start before retirement and stop after the person's plan-end year. Neither
benefit nor employment surplus is automatically saved. Only explicit
contributions add funds. After a plan ends, the survivor uses their own original
income for the target and their own return regime for inherited accounts.

## Walk through a fictional year

The provided example's first year is **2026**, t=0. The client retires in 2026;
the spouse continues working until 2029. Both plans are active.

| Step | Nominal CAD, displayed to cents |
|---|---:|
| Opening household savings | 495,000.00 |
| Spouse contributions, before growth (1,000 + 5,000 + 3,000) | 9,000.00 |
| Gross target (60,000 + 50,000) | 110,000.00 |
| Working spouse's employment income | 50,000.00 |
| Client's fixed pension | 18,000.00 |
| Client CPP: 18,092 × 200/365 | 9,913.42 |
| Client OAS: 8,908 × 200/365 | 4,881.10 |
| Beginning-of-year draw needed | 27,205.48 |
| Investment return after the draw | 22,285.53 |
| Closing savings | 499,080.05 |
| Unmet target | 0.00 |

There are 200 calendar days from June 15 through December 31, inclusive.
Available Cash is 36,000 after spouse contributions. The 27,205.479452 draw
is allocated pro rata: client has 25,000 of 36,000 and spouse has 11,000.
Remaining client assets earn 4%; remaining spouse assets earn 6%. Cash funds
the entire draw; RRSP and TFSA are untouched except for contributions and growth.

Reconciliation at full precision is
495,000 + 9,000 − 27,205.479452054795 + 22,285.52511415525
= 499,080.0456621004. Display rounding can produce a one-cent discrepancy if
you add the individually rounded table amounts. Today's-dollar values equal
nominal values in this first year. In 2027 spouse RRSP contribution becomes
5,000 × 1.025 = 5,125; its purchasing power is 5,125 / 1.02 = 5,024.5098.

The example ends in 2033 with nominal savings 512,320.5542, or 446,005.8731
in 2026 purchasing power. All 8 projected retirement years are funded.

## Audit and verification

Each account satisfies, apart from floating-point roundoff:

```text
closing = opening + contribution − withdrawal + investment return
retirement funding gap = investment draw + raw unmet spending
```

CSV and JSON suffixes `_nominal_cad` and `_today_cad` identify the units. Today's
values use the opening year's purchasing power and exponent `year − start_year`
for all amounts in a row, including closing balances. This is a year-labeled
reporting convention; it does **not** apply an additional year's inflation to
December 31 balances. A future exact-date valuation could use a different
deflator, but it would need to be labeled as a timing change.

`spending_target` is FRESH's gross income target; unmet spending is its unfunded
portion. There is no tax column because the source calculates no taxes. The
original tiny-shortfall convention treats raw gaps below CAD 0.000001 as zero.
`raw_unmet_spending` makes those small remainders visible. No materially negative
account balance or asset overdraft is allowed. Reports do not round inside the
engine; binary floating-point follows the source's Number arithmetic.

Run `python -m unittest discover -v` for hand-calculated and invariant checks.
To execute the recovered TypeScript engine as the reference, also install Node.js
22.18+ or 24+ and run:

```text
python tests/verify_original.py
```

No npm installation is needed: Node can run the source TypeScript after removing
type annotations. This command reads the unchanged `original_fresh/src/model.ts`,
compares every original annual field and summary metric, and writes
`verification_results.json`. It does not push changes or query financial services.

The original source cannot accept a rate different from 0/inflation. Those cases
use a separately loaded copy with **only the contribution expression replaced**;
they are marked as a formula extension, not claimed as unchanged-model parity.
Independent hand-calculated tests check 2.5%, 0%, and separate inflation.

Observed results: **18 Python tests passed; 23 comparison scenarios passed**.
The 18 unchanged-source scenarios differed by at most CAD 0.00000000093133
(the original 54-year spouse example); 16 matched exactly. The 5 formula-extension
scenarios differed by at most CAD 0.00000000005821. These are binary floating-point
roundoff differences far below a cent. Comparison tolerance is absolute CAD 1e-8 or relative
1e-12. Annual account reconciliation also passed for every comparison row.
See [verification results](verification_results.json) and
[verification notes](VERIFICATION.md) for reproducible evidence and limitations.

## Remaining limitations

The original engine is gross pre-tax, deterministic, and annual. It has no income
tax, OAS clawback, GIS, RRIF minimums, LIF maximums, contribution limits, pension
splitting, fees, estate tax, legal transfer mechanics, survivor pensions or CPP
survivor benefits. RRSP and TFSA dollars therefore do not imply equal after-tax
spending power. No simulations were present or introduced. Real household
spending and survivor needs may differ from the fixed income-replacement target.

The local Python planner has editable inputs, area graphs and separate
client/advisor PDF reports. CSV/JSON files are generated through `main.py`.
The standalone HTML is a saved snapshot.
The original React application remains available in `original_fresh/` for reference.
Future financial enhancements should be specified and tested separately so they
do not quietly change FRESH's assumptions.
