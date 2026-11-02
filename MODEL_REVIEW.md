# Model lineage and implementation differences

This document compares the current Python and browser implementations with the
preserved TypeScript reference. For the current formulas and user-facing
assumptions, start with the [model guide](docs/model.md).

The baseline is FRESH commit `a0623571bd85c0c75c284efe4ba4dee550db8d9b`.
Its calculation, model tests, interface, charts, PDF code, README and specification
were reviewed. The unchanged files are retained in `original_fresh/`; see
[source provenance](docs/provenance.md) for the source manifest and archival scope.

## Baseline calculation

The reference calculates a deterministic Canadian-dollar household projection
from the opening calendar year through the latest plan-end year, inclusive.
It supports up to two people with independent retirement dates and account
ownership, three account types, fixed annual returns and gross income
replacement. It is not a complete household budget.

1. Start with each person's Cash, RRSP and TFSA balances.
2. In the year after one plan ends, transfer remaining balances by account type
   to the active spouse. Future growth uses the spouse's return regime.
3. Add contributions for active people still working. Flat contributions remain
   unchanged; indexed contributions compound with general inflation from the
   opening year. No contribution occurs in a person's retirement year, although
   a still-working spouse can contribute.
4. Beginning in the first person's retirement year, set the target to the sum
   of original current incomes for active people, compounded with inflation.
   Count working employment income, pensions and CPP/OAS toward this target.
5. Withdraw the remaining gap in the selected household account order. Allocate
   each account type's withdrawal pro rata to its owners' available balances.
6. Apply each owner's before/after-retirement return to remaining balances.
   Record shortages and balances after growth.

Baseline CPP/OAS use the supplied 2026 reference amounts, entitlement percentage,
start-age or deferral adjustment, inflation from 2026 and exact-day birthday
proration in the first payment year. Benefits stop after the person's plan-end
year. CPP can start independently of retirement. Baseline pensions begin in the
retirement year and remain fixed in nominal dollars.

The original outputs include annual income components, contributions,
withdrawals, shortages and account balances, plus retirement and final savings,
the first-year target, funded retirement years and the first shortage. Working
employment income funds the target but is omitted from the original visible
income table/chart.

## Retained assumptions and implementation differences

| Topic | Baseline behavior | Current implementation |
|---|---|---|
| Midyear start | Models the whole opening year, including full contributions | Retained; explicit `as_of` makes scenarios reproducible |
| Retirement timing | January 1 of the age-attainment year | Retained; only benefits receive birthday proration |
| Plan-end timing | Only the calendar year affects the projection | Retained and documented |
| Contribution indexation | Flat or indexed to general inflation | Independent numeric annual rate for each account contribution |
| Pension indexation | Fixed nominal pension | Optional annual rate for each person, as described below |
| Return timing | Withdrawals precede growth | Retained; subsequent growth cannot erase that year's shortage |
| Savings at retirement | Opening household savings before contributions | Retained, including before a still-working spouse's contributions |
| Funded years | Counts all funded retirement years | Retained; first shortage remains visible even if later years are funded |
| Very small shortages | Gaps below CAD 0.000001 count as zero | Retained in the verdict; raw remainder is available for audit |
| Income chart | Excludes working salary even though it funds the target | Retained with an explanation |
| Gross target | 100% of entered current gross income; contributions are not deducted from available income | Retained; not an after-tax spending budget |
| Benefit reference values | Fixed 2026 assumptions extrapolated with inflation | Retained without asserting current legal entitlements |
| Surplus income | Not added to accounts | Saved to Cash after either person retires, as described below |
| Extreme values | Finite inputs can overflow during compounding | Python rejects unrepresentable results explicitly |
| Balance audit | No opening/growth/account-withdrawal columns | Reconciliation fields are available in Python data exports |
| Display precision | Whole-dollar display | Dashboard, HTML and PDFs use whole dollars; CSV/JSON retain precision |

### Pension indexation

Each person has a separate annual pension-indexation percentage, defaulting to
zero. The entered pension is payable in the retirement year (t=0); increases
begin the following year. For already-retired people, elapsed retirement years
are included, so the input is the retirement-year amount, not today's payment.
At 0%, pension payments match the baseline fixed pension. The advisor PDF lists
all rates, including those whose input controls are collapsed.

This changes an assumption available to the user; it is not a correction to the
baseline pension formula. Surplus-saving cases also require the treatment below.

### Retirement-income surplus saving

Once either person retires, household employment, pension, CPP and OAS income
above the household target is saved to Cash before growth. A person's positive
income excess over their own target share determines their allocation weight.
Only the net household surplus is saved, after covering everyone's target.
Each Cash account retains its owner's applicable return rate.

Before either person retires, only entered contributions add savings. CPP/OAS
start-age rules remain independent of retirement. There is no separate surplus
column; contribution fields continue to mean entered contributions.

Reference comparisons with excess income use an explicitly labelled in-memory
extension rather than claiming agreement with the unchanged baseline. The
[verification guide](VERIFICATION.md) describes comparison coverage and limits.

## Interpretation and remaining scope

The baseline source review found no substantive calculation contradiction
between the reviewed implementation and specification. This is an assessment
of implementation consistency, not certification of financial assumptions.

The current implementations add numeric contribution rates, pension indexation,
retirement-surplus saving, explicit scenario dates, real-value data exports,
reconciliation fields and validation. Both interfaces provide client and advisor
PDFs; Python also exports CSV, JSON and a standalone HTML snapshot.

The model still excludes after-tax cash flows, RRIF/LIF rules, clawbacks,
contribution limits, fees, actual survivor entitlements, household spending
budgets, variable returns and Monte Carlo simulations. These are substantive
model limitations, not missing verification steps. See the [model guide](docs/model.md)
for the complete assumptions.

[Back to the README](README.md).
