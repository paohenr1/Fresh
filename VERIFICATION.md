# Calculation and interface verification

FRESH uses hand-calculated tests, account-reconciliation checks, cross-language
comparisons and browser interaction tests. These checks establish arithmetic
agreement for covered scenarios. They do not certify government reference
amounts, validate economic assumptions or cover every possible input.

## Reproduce the checks

Use Python 3.11 or newer and Node.js 24 or newer. Install Python dependencies
using the [README setup commands](README.md#run-locally-with-python), then
install browser dependencies from the repository root:

```text
npm ci --prefix web
```

Run the following on Windows:

```text
.venv\Scripts\python.exe -m unittest discover -s tests -v
.venv\Scripts\python.exe tests/verify_original.py
.venv\Scripts\python.exe tests/verify_browser.py
npm test --prefix web
npm run build --prefix web
npm run test:browser --prefix web
node --check planner.js
```

With the project environment activated, `python` can replace the explicit
Windows interpreter path. Windows browser tests require installed Microsoft
Edge; CI installs Chromium on Linux. A missing browser is an unmet prerequisite,
not a passing test. See the [browser guide](web/README.md) for frontend setup.

The comparison scripts regenerate `verification_results.json` and
`browser_verification_results.json`. Reports and browser test artifacts belong
in ignored `output/`, `tmp/`, `web/test-results/` and `web/playwright-report/`.

## What is checked

### Annual balances and funding

Each account satisfies, apart from floating-point roundoff:

```text
closing = opening + contribution + saved retirement-income surplus − withdrawal + investment return
retirement funding gap = investment draw + raw unmet spending
```

Only Cash receives saved surplus. It is derived as
`max(0, employment + pension + CPP + OAS − target)` in retirement years and is
zero before either person retires. Contribution fields contain only entered
contributions; saved surplus has no separate annual output column.

Hand-calculated and invariant tests cover saving, growth, partial-retirement
allocation, withdrawals, depletion and survivor years. No materially negative
account balance or asset overdraft is allowed.

### Reporting units and precision

CSV and JSON suffixes `_nominal_cad` and `_today_cad` identify units. Today's
values use the opening year's purchasing power and exponent `year − start_year`
for all amounts in a row, including closing balances. This year-labelled
convention does not apply an extra year's inflation to December 31 balances.

`spending_target` is the gross income target, not an after-tax spending budget.
The shortfall verdict treats raw gaps below CAD 0.000001 as zero;
`raw_unmet_spending` retains those small remainders. Calculations do not round
inside the engine and use binary floating-point arithmetic.

### Cross-language and reference comparisons

`tests/verify_browser.py` compares the active browser and Python engines,
including annual account-reconciliation fields.

`tests/verify_original.py` reads the unchanged TypeScript calculation in
`original_fresh/src/model.ts` and compares annual fields and summary metrics.
Node runs this reference without installing its npm dependencies. The reference
files are not edited by the comparison harness.

The original engine supports only flat or inflation-indexed contributions and
does not save retirement-income surplus. Cases requiring numeric contribution
rates or surplus saving use a separately loaded, in-memory extension of that
reference. Unchanged-model cases and extension cases are distinguished in the
results; intentional final-balance differences are not presented as roundoff
or unchanged-model agreement. See the [model comparison](MODEL_REVIEW.md) and
[source provenance](docs/provenance.md) for the baseline and extensions.

### Browser interaction and exports

Browser tests use a local server and cover editable inputs, invalid-result
handling, nominal tables, PDF downloads, long reports, surplus saving and mobile
layout. The preserved reference interface is not rebuilt or tested as the
current application.

## Recorded results

The last recorded full verification in the documentation is **October 14,
2026**: 41 Python tests, 24 browser model tests, 5 browser interaction/PDF tests,
23 original-source/extension comparisons and 36 browser/Python comparison
scenarios passed. The browser production build and `planner.js` syntax check
also passed. These are dated results, not a claim that a new test run has occurred.

For equivalent calculations, the recorded maximum differences are below
CAD 0.000000001. Comparison tolerance is absolute CAD 1e-8 or relative 1e-12.
The tracked [original-source results](verification_results.json) and
[browser/Python results](browser_verification_results.json) provide scenario-level
comparison data; they are not complete logs of every interface or visual check.

The [Python CI workflow](.github/workflows/python.yml) runs Python tests,
original-source comparisons and the JavaScript syntax check on pull requests.
The [Pages workflow](.github/workflows/pages.yml) runs browser/Python comparisons,
browser tests and the production build before publishing pushes to `main`.
A passing Python workflow alone does not establish that browser tests ran.

See [historical verification](docs/verification-history.md) for earlier records,
coverage details and the distinction between past and current report layouts.
