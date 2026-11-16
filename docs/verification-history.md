# Historical verification records

These records describe earlier development checks. Test counts, report layouts
and environment versions belong to the versions tested, not necessarily a new
checkout. Use the [verification guide](../VERIFICATION.md) for reproducible
commands and the [usage guide](usage.md) for the current interface.

The [October 14, 2026 documentation snapshot](https://github.com/paohenr1/Fresh/blob/8b7d9e7396444771433cdf777f00a83ec012bbed/docs/verification-history.md)
retains the earlier detailed record. Historical visual-inspection statements below
are reported observations, not fresh browser checks or publicly attached image
artifacts. Tracked numerical comparison files provide separate, inspectable
evidence for the scenarios they cover.

## October 14, 2026: documentation and source-formatting checks

The recorded cleanup run passed 41 Python tests, 24 browser model tests,
5 browser interaction/PDF tests, 23 original-source comparisons and
36 browser/Python comparisons. The browser build, JavaScript syntax check,
example exports and local documentation-link checks also passed.

The record reports unchanged hashes for reference files, Python calculation
code, dependencies and numerical comparison records. The browser build retained
its warning about a bundle larger than 500 kB. A new clean-machine installation
and external deployment were not performed as part of that run.

## October 14, 2026: retirement-income surplus saving

Net household income above the target is added to Cash after either person
retires, before growth. Positive personal income excesses determine allocation,
and each Cash account retains its owner's return rate. Entered contributions
remain distinct from saved surplus; no additional annual column was added.
CPP/OAS can still begin at selected ages before retirement.

The recorded run passed 41 Python tests, 24 browser model tests and 36
browser/Python comparisons, including surplus accumulation, partial-retirement
allocation, different owner return regimes, subsequent depletion and
reconciliation. The maximum numerical difference was 9.31322574615e-10 CAD.

The 23 original-source comparisons passed with a labelled in-memory surplus
extension where necessary. Intentional final-balance differences from the
legacy behavior are recorded in `verification_results.json`; cases without
surplus retain their unchanged-source comparison. Reference files were not
modified. At this stage dashboards and PDFs used nominal CAD without a
dollar-basis selector.

## October 13, 2026: simplified advisor export

The advisor report included all inputs, five summary metrics, both graphs and
the compact dashboard annual table, without separate reconciliation tables.
The example decreased from ten pages to five. At that time its annual table
followed the dashboard's nominal/today's-dollar selection; that selector is no
longer part of the current interface.

All 25 tests passed. The record reports visual inspection of all five example
pages and separate checks of today's-dollar values and the final year of a
long individual plan.

## October 13, 2026: dashboard and separate PDF exports

The dashboard added Current savings and separate client/advisor PDF exports.
All 25 calculation and HTTP tests passed, including both PDF routes and invalid
export-input rejection. ReportLab 4.5.1 was recorded in the test environment.

The example client PDF had three pages and the advisor PDF ten pages. The record
reports Poppler rendering and visual inspection, plus checks of edited balances,
high-precision contribution rates, a 30-year individual projection and depletion.
Parsed-text checks covered complete inputs, the final year, page totals and
nominal/today's-dollar labels. This update did not change the calculation engine;
export timestamps used UTC. These page counts describe that earlier layout.

## Original Python/reference comparison

The original comparison was recorded with Python 3.14.8 and Node.js 24.21.0
against reference commit `a0623571bd85c0c75c284efe4ba4dee550db8d9b`.

Eighteen Python test methods passed, including parameterized invalid-input
checks. Twenty-three source cases passed: eighteen against the unchanged engine
and five against a separately loaded numeric contribution-indexation extension.
These historical results predate the surplus-saving extension described above.

Coverage included positive, zero and negative contribution indexation;
indexation unequal to inflation; zero and negative returns; depletion; ordered
and proportional withdrawals; separate retirement dates and returns; survivor
transfers; CPP early/late starts; OAS deferral; exact-day and leap-birthday timing;
benefits before retirement; starting after the reference year; funding restored
after a shortage; zero-asset funded scenarios; invalid inputs; and per-account
annual reconciliation.

All original annual fields and summary metrics were compared in unchanged-model
cases. Sixteen scenarios matched exactly. The 51-year and 54-year defaults
differed by at most 2.3283064365386963e-10 and 9.313225746154785e-10 CAD. The
largest numeric-indexation extension difference was 5.820766091346741e-11 CAD.
These differences were attributed to cross-runtime floating-point roundoff,
not changes to cash-flow timing.

The fictional example opened 2026 with CAD 495,000 and closed with
499,080.0456621004. Its 2033 closing balance was 512,320.55416591745 nominal,
or 446,005.87314226036 in 2026 dollars. The command-line example generated
CSV, JSON and HTML reports. The original reference UI/PDF tests were inspected
but not rerun during this calculation-port check.

## October 8, 2026: interactive Python planner

The local planner in `app.py` reused the Python calculation engine. All 23 tests
passed: eighteen calculation tests and five HTTP interface tests. Coverage
included editable inputs, changed inputs matching direct engine results,
current CSV/JSON data, invalid inputs without stale results, spouse exclusion,
zero contribution indexation and rejection of unrelated-site requests.
JavaScript syntax checks also passed.

These were automated calculation and HTTP checks, not a completed visual browser
review. No financial formulas were added by this interface change.

## Limits of the historical evidence

The checks establish arithmetic agreement and reconciliation for the scenarios
covered. They do not validate economic assumptions or government reference
values against regulations, and they do not exhaust every possible input.

[Back to the README](../README.md).
