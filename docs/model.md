# Inputs, formulas and assumptions

Run commands from the repository root.

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
   Once either person retires, income above the household target is added to
   Cash before annual investment growth. Income includes employment, pension,
   CPP and OAS. Entered contributions are separate and are not income.
   Allocate the net surplus proportionally to active people whose own income
   exceeds their inflation-adjusted share of the target. Each person's Cash
   keeps its existing working/retired return regime. A working person's salary
   alone equals their target share; early CPP/OAS can create a personal excess.
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
start before retirement and stop after the person's plan-end year. Before either
person retires, only explicit contributions add funds. Once either retires,
income above the household target is added to Cash before growth. After a plan
ends, the survivor uses their own original
income for the target and their own return regime for inherited accounts.


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

[Back to the README](../README.md).
