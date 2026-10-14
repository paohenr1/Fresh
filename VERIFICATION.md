# Calculation and interface verification

## Repository cleanup verification — October 14, 2026

After documentation reorganization and browser source formatting, all 41 Python
tests, 24 browser model tests, 5 browser interaction/PDF tests, 23 original-source
comparisons and 36 browser/Python comparisons passed. The production browser
build and `planner.js` syntax check passed. Both example file-export commands,
including an explicit starting-date override, completed successfully.

Formatting the backed-up browser source produced the same cleaned source, with
only the documented removal of unused CSS rules and one comment update.
All reference files, Python financial calculation code, dependencies and numeric
comparison records retained their pre-cleanup SHA-256 hashes. Local documentation
links were checked. The build still reports a bundle larger than 500 kB; no
loading or dependency changes were made. A new clean-machine installation and
external deployment were not performed for this cleanup.

## Audit and verification

Each account satisfies, apart from floating-point roundoff:

```text
closing = opening + contribution + saved retirement-income surplus − withdrawal + investment return
retirement funding gap = investment draw + raw unmet spending
```

Only Cash receives the saved surplus. It can be derived from existing income
fields as `max(0, employment + pension + CPP + OAS − target)` in retirement
years, and is zero before either person retires. No surplus column or separate
annual output field is added; entered contribution fields retain their meaning.

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
use a separately loaded copy with the contribution expression replaced.
Cases with retirement income above the target also require an in-memory
surplus-saving extension of the old source. Neither extension edits
`original_fresh/`. Cases without surplus compare all original fields unchanged;
cases with surplus explicitly report their intentional difference in final
savings from the old behavior. This is an intentional change, not roundoff or a fix.
Independent hand-calculated tests check saving, growth, partial-retirement
allocation, subsequent withdrawal/depletion and survivor years.

Current results: **41 Python tests, 24 browser model tests and 36 browser/Python
comparison scenarios passed**. The 23 original-source/extension comparisons also
passed. Floating-point differences in equivalent calculations remain below
CAD 0.000000001. Comparison tolerance is absolute CAD 1e-8 or relative 1e-12.
Cash reconciliation includes the derived saved surplus; no surplus column is
added, and contribution fields still contain only entered contributions.
See [original-source comparison results](verification_results.json) and
[browser/Python results](browser_verification_results.json) for reproducible evidence and limitations.


## Browser checks

Use Node.js 24 or newer for the reference comparisons and browser development.
Install browser dependencies from the repository root with `npm ci --prefix web`.

```text
.venv\Scripts\python.exe -m unittest discover -s tests -v
.venv\Scripts\python.exe tests/verify_original.py
.venv\Scripts\python.exe tests/verify_browser.py
npm test --prefix web
npm run build --prefix web
npm run test:browser --prefix web
node --check planner.js
```

Windows browser tests require installed Microsoft Edge. The current Playwright
configuration uses Edge outside CI; CI installs Chromium on Linux. A missing
browser is an unmet prerequisite, not a passing test. The browser tests cover
editable inputs, invalid-result handling, nominal tables, PDF downloads,
long reports, surplus saving and mobile layout. They use a local test server.

The comparison scripts regenerate the two tracked numeric-result JSON files.
Generated reports and browser test artifacts belong in ignored `output/`,
`tmp/`, `web/test-results/` and `web/playwright-report/` directories.

These checks establish arithmetic agreement for the covered cases. They do not
certify government reference amounts, validate economic assumptions, or test all
possible inputs. The recovered reference UI is not rebuilt or changed.

See [historical verification](docs/verification-history.md) for earlier interface
and PDF checks. Historical counts and report layouts are not current results.
