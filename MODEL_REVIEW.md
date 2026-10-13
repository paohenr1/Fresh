# Source review before the Python implementation

Source recovered from `https://github.com/paohenr1/Fresh`, commit
`a0623571bd85c0c75c284efe4ba4dee550db8d9b` (the published cloud build).
The unchanged checkout is retained in `original_fresh/` for inspection and comparison.
Reviewed `src/model.ts`, `src/model.test.ts`, `src/App.tsx`, `src/Charts.tsx`,
`src/pdf.ts`, `README.md`, and `docs/specification.md`. No Excel workbook or
spreadsheet formulas exist in this source. Its formulas are TypeScript functions.

## What the current model calculates

A deterministic Canadian-dollar household projection from the opening calendar
year through the latest plan-end year, inclusive. It uses independent retirement
dates and ownership for up to two people, three account types, fixed annual
returns, and gross income replacement. It is not a full household budget.

1. Start with each person's Cash, RRSP and TFSA balances.
2. In the year after one plan ends, transfer remaining balances by account type
   to the active spouse. Future growth uses the spouse's return regime.
3. Add contributions for active people still working. Flat means unchanged;
   the original indexed option compounds contributions with general inflation
   from the projection opening year. No contribution occurs in a person's
   retirement year. A working spouse can still contribute in that year.
4. Beginning in the first person's retirement year, set the target to the sum
   of original current incomes for active people, compounded with inflation.
   Count working employment income, fixed pensions, and CPP/OAS toward this target.
5. Withdraw any remaining income gap following the selected household account
   order. Allocate each type's withdrawal pro rata to the owners' balances.
6. Apply the before/after-retirement return to each owner's remaining balances.
   Record shortage and balances after growth.

CPP/OAS are the supplied 2026 reference amounts multiplied by entitlement
percent, start-age/deferral adjustment, inflation from **2026**, and first-year
exact-day birthday proration. Benefits stop after the relevant plan-end year.
CPP starts independently of retirement. Pensions start in each person's
retirement year and remain fixed in nominal dollars.

Original outputs: annual target, employment (calculated, but omitted from the
original visible table/chart), pensions, CPP/OAS, contributions, draws, shortages,
account balances and total; first retirement savings, final savings, first-year
target, all fully funded retirement years, and first shortage. Two charts and a
browser-generated PDF present these results.

## Ambiguities, limitations, and potential errors

The reviewed specification resolves the earlier cloud conversation's timing
ambiguities. Where earlier discussion differs, this port follows the final
specification and the implemented engine together.

| Issue | Source behavior | Treatment in Python |
|---|---|---|
| Midyear starting date | Whole current year, including full contributions | Preserved; explicit `as_of` date makes tests reproducible |
| Retirement birthday | January 1 of age-attainment year | Preserved; only benefits receive birthday proration |
| Exact plan-end date | Only the year affects the projection | Preserved and documented |
| Contribution indexing scope | Only six possible person/account contribution switches | Replace those switches alone; pensions remain fixed |
| Return timing | Draws precede growth; depleted assets cannot earn their way out of that year's shortage | Preserved |
| Savings at retirement | Opening household savings before all contributions, including working spouse's | Preserved |
| Funded years | Counts all funded retirement years, not consecutive years before first shortage | Preserved; first shortage remains visible |
| Very small shortages | Remainder below CAD 0.000001 becomes zero | Preserved in verdict; raw remainder added for audit |
| Income chart | Working salary excluded even though it funds the target | Preserved with explicit explanation |
| Gross target | 100% of current gross income; working contributions are not deducted from available income | Preserved; no after-tax spending inference |
| Benefit reference values | Supplied fixed 2026 figures, extrapolated with inflation | Preserved without asserting these are current legal entitlements |
| Surplus income | Not added to accounts | Preserved; only entered contributions build savings |
| Extreme values | Finite inputs can overflow during compounding | Python rejects unrepresentable results explicitly |
| Balance audit | Original has no opening/growth/account-draw columns | Add them without changing the calculation |
| Display precision | Original money displays whole dollars | Python CSV/JSON retain precision; HTML rounds to cents |

No substantive calculation contradiction between the final source and
specification was found. No financial calculation fixes were imposed. This is
a reproduction of the implemented model, not certification of its assumptions.

## Worthwhile improvements and their scope

Implemented: numeric contribution rates, inflation-separated real values,
explicit date, account reconciliation data, stronger invalid-input errors,
independent numerical tests and comparisons to original source.

Future options requiring an explicit financial specification: after-tax cash
flows, RRIF/LIF rules, clawbacks, contribution limits, fees, actual survivor
entitlements, spending patterns, cash-flow budgets, variable returns or
Monte Carlo simulations. No such features exist in the source engine, and none
were added. A future interface could restore its dedicated styled PDF exporter;
this version produces a local printable HTML report instead.
