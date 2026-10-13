# Verification of the Python port

## Simplified advisor export - October 13, 2026

The advisor report now includes every input, five summary boxes, both graphs
and only the compact dashboard annual table. Extra audit/reconciliation tables
are omitted. The example is now 5 pages (previously 10), and the annual table
follows the dashboard's nominal/today's-dollar selection. All 25 existing tests
passed. All five example pages were rendered and visually inspected; separate
checks verified today's-dollar values and the final year of a long individual
plan. Earlier full-audit report checks below are historical.

## Dashboard and PDF update - October 13, 2026

Added the Current savings card and separate client/advisor PDF exports. The
pre-change project backup is in `backups/`, with an SHA-256 manifest. All 25
calculation and HTTP tests passed using `.venv/Scripts/python.exe -m unittest
discover -v`. The HTTP tests cover both PDF routes and rejection of invalid
export inputs. ReportLab 4.5.1 is installed in the project environment.

The example client PDF has 3 pages; the advisor PDF has 10. PDF pages were
rendered with Poppler and visually inspected. Additional checks cover edited
balances, high-precision contribution rates, a 30-year single-person projection
and asset depletion. Parsed PDF text confirms complete inputs, the final
projection year, page totals, and correctly labelled nominal/today's-dollar
sections. Results are in `pdf_verification_results.json`. This update does not
change the financial calculation engine. Export timestamp labels use UTC.

## Original calculation comparison

Verified locally with Python 3.14.8 and Node.js 24.21.0 against FRESH commit
`a0623571bd85c0c75c284efe4ba4dee550db8d9b`.

Commands:

```text
python -m unittest discover -v
python tests/verify_original.py
python main.py
```

18 Python test methods passed, including parameterized invalid-input checks.
23 source comparison cases passed: 18 against the original engine unchanged,
5 against a separate copy with only the authorized indexation expression changed.
Detailed counts, row counts and maximum numerical differences appear in
`verification_results.json`.

Coverage includes zero/positive/negative indexation, contribution growth unequal
to inflation, 0 returns, negative returns, depletion, ordered withdrawals,
proportional spouse withdrawals, separate retirement dates and returns, survivor
transfers, CPP early/late start, OAS deferral, exact days, leap birthdays, benefits
beginning before retirement, a projection beginning after the reference year,
first shortage followed by later fully funded years, zero-asset funded scenarios,
invalid inputs and per-account annual balance reconciliation.

For unchanged-model cases all original output fields were compared, including
annual contribution, income, draw, shortage, balances, ages and summary metrics.
16 scenarios matched exactly. The 51-year and 54-year original default scenarios
differed by at most 2.3283064365386963e-10 and 9.313225746154785e-10 CAD respectively.
For the numeric-rate extension the largest absolute difference was
5.820766091346741e-11 CAD in the fictional spouse scenario. This comes from
floating-point exponentiation/roundoff between runtimes; calculation timing and
financial assumptions were preserved. Display differences (whole dollars in
the website versus cents in HTML and full precision in data exports) are
presentation choices only.

The example ran successfully and wrote all three reports. Its 2026 opening
balance is CAD 495,000; closing balance is 499,080.0456621004. Its 2033 final
balance is 512,320.55416591745 nominal / 446,005.87314226036 in 2026 dollars.

These tests establish parity for the covered scenarios and arithmetic
reconciliation. They do not validate the economic assumptions or government
reference values against current regulations, and they are not exhaustive over
all possible inputs. No workbook was available in the recovered repository.
The original browser UI/PDF tests were inspected but not rerun, since this port
does not change or rebuild that UI.
# Interactive planner verification — October 8, 2026

The local planner added in `app.py` uses the existing Python calculation engine.
All 23 tests passed (`python -m unittest discover -v`): the original 18 calculation
tests and five HTTP interface tests. The new tests cover editable input markup,
changed financial inputs matching direct Python results, current CSV/JSON data,
invalid inputs without stale results, spouse exclusion, zero contribution
indexation, and rejection of requests from an unrelated website. JavaScript
syntax checks also passed. These are automated code/API checks, not a completed
visual browser review.

The earlier numerical source-comparison results below remain a record of the
calculation engine verification; this interface change adds no financial formulas.
