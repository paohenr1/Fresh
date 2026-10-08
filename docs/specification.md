# Fresh — reviewed build specification

This specification consolidates the decisions agreed during the review of
`fresh-build-prompt.md`.

## Purpose and scope

Build a single-page, client-side retirement projection calculator called Fresh.
Give a deterministic, pre-tax illustration of whether household income and
savings fund the income target through the planning horizon.

All calculations and PDF generation happen in the visitor's browser. No backend,
storage, saved scenarios, or transmission of financial inputs. Nothing is saved
between visits.

## Inputs

### Household

- Client date of birth; display current age.
- Optional "Add spouse" toggle revealing the spouse's equivalent fields.
- Separate retirement age for each person.
- Separate **Plan end date** for each person. Supporting text explains that the
  person's income ends after that calendar year and remaining savings stay
  available to a surviving spouse. Do not label this input "death date."
- **Current income ($/year)** for each person, with a short explanation that this
  means income before tax.
- No income-target percentage input: always use 100% of current income.

### Savings

For each person, separately for Cash, RRSP, and TFSA:

- Current balance.
- Annual contribution.
- Contribution indexing: Flat by default, or Indexed to inflation.

Shared household settings:

- Expected return before retirement (%).
- Expected return during retirement (%).
- Inflation (%).
- Withdrawal order; default Cash → RRSP → TFSA.

### Pension and government benefits

For each person:

- **Annual pension payable at retirement ($/year)**. This is the expected nominal
  payment when that person retires, not an amount in today's dollars. It remains
  fixed thereafter; no pension indexing input in this version.
- CPP: percentage of maximum and start age, 60–70.
- OAS: percentage of maximum and deferral years, 0–5; starts at age 65 plus deferral.

Keep CPP/OAS reference annual maximums and their reference year together in one
clearly labelled configuration location so they can be updated to actual
government figures later. Initially use the supplied 2026 reference figures:
CPP $18,092/year and OAS $8,908/year. No live government-rate connection is required.

## Annual timeline

- Use calendar-year rows, beginning with the current calendar year.
- Treat the current year as a full projection year. Do not prorate it based on
  the date the calculator is opened.
- Display the age each person reaches during each calendar year. The current-age
  display beside date of birth still reflects their actual age today.
- A person retires at the beginning of the year they reach their retirement age.
- Their employment income and contributions stop in their retirement year.
  There is no final contribution in that year.
- Their pension starts in their retirement year.
- Model each Plan end date as the end of its calendar year. That person's income,
  benefits, and contributions cease in following years.
- End the household projection in the later of the two Plan end years, or the
  client's Plan end year if there is no spouse.
- Explain briefly that the model uses annual approximations for retirement and
  plan endpoints. CPP/OAS start-year birthday prorating remains a specific exception.

## Income target and partial retirement

Use the projection's starting year as the baseline for user-entered current income
and indexed contributions. Do not apply the government-benefit reference year to
these inputs.

For each year starting when the first person retires:

1. Take the original current incomes of the people whose plans remain active.
2. Add those incomes together.
3. Increase the sum with inflation from the projection's starting year.

That is the household income target. It is always 100%, with no target-percentage
control. After one person's plan ends, only the survivor's original current income
contributes to the target; continue the same inflation adjustment.

While a person is still working, their original current income grows with inflation
and counts as employment income available to meet the household target. Their
entered contributions continue until their own retirement or plan end.

Once either person retires, count employment income, pensions, CPP, and OAS from
both people toward the target whenever those income sources are active. Withdraw
from investments to cover the remaining gap.

Income is not automatically invested. Only entered account contributions add to
savings. Do not automatically save surplus salary, pension, or benefits. CPP/OAS
received before either person retires does not automatically add to savings.

This is a projection based on gross income and entered contributions, not a complete
household cash-flow budget.

## Pension, CPP, and OAS calculations

- Pension: the entered annual payment begins at the person's retirement and stays
  fixed in nominal dollars. It stops after their Plan end year.
- CPP: multiply the reference maximum by the entered percentage of maximum and
  the start-age adjustment. Adjustment is −0.6% per month before age 65 and +0.7%
  per month after age 65, bounded between 64% and 142% of the reference maximum.
- OAS: multiply the reference maximum by the entered percentage of maximum and
  the deferral adjustment. Each deferral year adds 0.6% per month of deferral.
- CPP/OAS maximums increase with the entered inflation rate from their reference
  year to each projection year. Explain that this extrapolates reference rates;
  it does not fetch future government amounts.
- In the calendar year of the CPP/OAS start birthday, prorate the payment by exact
  calendar days from the birthday to year-end divided by the days in that year.
  Subsequent active years receive a full annual payment.
- CPP/OAS start ages remain independent of retirement ages. Benefits can begin
  while someone is still working.
- Each person's benefits stop after their Plan end year.

## Investment calculations

- Contributions and withdrawals occur at the beginning of each year, before growth.
- Flat contributions stay at the entered amount. Indexed contributions grow with
  inflation from the projection's starting year.
- Apply the before-retirement return to each person's accounts until their own
  retirement year. Apply the during-retirement return starting in that year.
  Keep just the two shared return inputs, even when retirement dates differ.
- Beginning in the first retirement year, calculate:

  `gap = max(0, target − employment income − pension − CPP − OAS)`

- Follow the selected account-type withdrawal order across the household.
- Within each type, split a withdrawal in proportion to each person's available
  balance. For example, Cash balances of $30,000 and $10,000 fund a $4,000 Cash
  withdrawal with $3,000 and $1,000 respectively.
- Both people's accounts are available, including a working spouse's accounts.
- Withdraw no more than the available balance. Record any unfunded remainder
  as that year's shortage.
- Apply the applicable return to the balances remaining after contributions and
  withdrawals. Table balances show the result after growth.
- After one person's plan ends, all remaining savings remain available to the
  survivor. Retain their Cash/RRSP/TFSA categories for this simplified projection;
  survivor-held balances follow the survivor's applicable return rate.
- Do not model tax, probate, or legal account-transfer mechanics.

## Outputs

Recompute live on every valid input change.

### Verdict and metrics

- **ON TRACK IN THIS SCENARIO** if all retirement-year targets are fully funded.
- Otherwise **SHORTFALL IN THIS SCENARIO**, identifying the first shortfall year.
- Zero investments alone do not establish a shortfall: ongoing income may still
  fully meet the target.
- **Savings at first retirement:** combined investments at the beginning of the
  first retirement year, before that year's contributions, withdrawals, or growth.
- **Balance left at plan end:** total balance after final-year growth.
- **Fully funded retirement years: x of y:** count all fully funded years from the
  first retirement year through the final plan year. A later funded year does not
  erase an earlier shortage.
- **First-year income target ($/year):** target in the first retirement year.

### Scenario at a glance

Show each person's retirement timeline and Plan end date, starting savings,
current incomes, income target, return assumptions, annual contributions,
withdrawal order, and the fixed-pension assumption.

### Charts

Display both charts together:

1. Stacked household investment balances by Cash, RRSP, and TFSA from the current
   year through the horizon. Mark each distinct retirement year.
2. Retirement income chart with stacked CPP, OAS, pension, and investment
   withdrawals, with the household income target overlaid.

Do not include employment income in the income chart. Include a short explanation
that working income counts in the calculation but is excluded from the chart,
so the displayed stack may fall below the target while one person still works
even when the year is fully funded.

### Full year-by-year table

Show calendar year, client age, spouse age when applicable, income target, shortage,
CPP, OAS, pension, investment draw, and Cash/RRSP/TFSA/total balances after growth.

Financial columns are household totals. Leave a person's age blank after their
Plan end year. Distinguish accumulation years, where no retirement target or
withdrawal applies, from retirement years.

## Client PDF export

An **Export client PDF** button generates the PDF entirely in the browser and
downloads `fresh-client-retirement-projection.pdf`.

- Page 1: title, prepared date, verdict, four metrics, scenario facts, disclaimer.
  Include each person's pension amount, CPP percentage and start age, OAS
  percentage and deferral, and the government reference amounts and year.
- Page 2: both charts and a short "How to read this" explanation, including the
  employment-income chart omission. Use coloured legends and a dashed target
  key. Put the working-income explanation beside the income chart and label
  the target transition after a person's plan ends.
- Page 3 onward: complete year-by-year table. Continue across additional pages
  as needed, with readable text, white headings on green, and repeated report
  titles and column headings. Mark retirement years with an asterisk and shade
  retirement and shortage rows distinctly.

On every export click, re-collect the current inputs and re-run the projection.
Never reuse a cached PDF or an earlier scenario.

## Validation

- Validate dates and each person's timeline. Each Plan end must follow retirement.
- Income, balances, contributions, pension, and percentages of benefit maximums
  must not be negative.
- Enforce CPP start ages of 60–70 and OAS deferral of 0–5 years.
- Require each account type exactly once in the withdrawal order.
- Allow negative investment returns so loss scenarios can be explored; reject
  values that make the annual financial calculations invalid.
- Show clear validation messages beside affected fields.
- A valid scenario with a financial shortfall must still calculate normally.
- Keep calculation precision; round values for display.

## Disclaimers and design

State that income targets, benefits, and balances are gross, pre-tax estimates.
RRSP and TFSA balances do not represent equal spendable income after tax.

Excluded: income taxes, OAS clawback, GIS, RRIF minimums, LIF maximums, pension
splitting, fees, survivor pension payments, and CPP survivor benefits. When a
person's plan ends, their income stops and their savings remain available; this
is a simplified assumption, not a calculation of estate or survivor entitlements.

Disclose annual timing approximations, fixed pension payments, and inflation-based
extrapolation of government reference amounts. Include:

**"Values are estimates, not guarantees."**

Use a clean, professional dark-green theme, clear section cards, readable charts
and tables, and plain language beyond standard account names and benefit names.
