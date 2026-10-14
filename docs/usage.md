# Running and exporting FRESH

Run commands from the repository root.

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
  dashboard. Dashboard tables and both PDF exports use nominal CAD.
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
python main.py examples/fictional.json --as-of 2028-10-08 --output output/2028
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
  are displayed. Expand the annual table to see the nominal CAD projection.
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
`python tests/verify_browser.py` compares 36 scenarios, including every annual
account reconciliation field. Results are recorded in
`browser_verification_results.json`; maximum observed difference is below
0.000000001 CAD. Browser whole-dollar display uses Python's ties-to-even rounding.
Reports use the same labels and figures; Python uses vector PDF graphs while
browser PDFs embed high-resolution images of the displayed graphs.

The Pages workflow runs calculation comparisons, model tests, browser interaction
tests and both PDF downloads before publishing `web/dist/`. The old browser
version stays on the backup branch. `original_fresh/` remains untouched for
original-source verification.

[Back to the README](../README.md).
