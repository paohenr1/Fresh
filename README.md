# Fresh

A deterministic, pre-tax retirement projection calculator. Runs entirely in the browser — nothing you enter leaves the page.

Enter household details, savings, pensions, and CPP/OAS. Fresh projects the balances year by year and reports whether the income target holds through the planning horizon, with charts, a year-by-year table, and a client PDF export.

Live: https://paohenr1.github.io/Fresh/

## Run it

Requires Node.js 22.12+.

```sh
npm ci
npm run dev
```

`npm test` runs the model tests. `npm run build` produces the static site in `dist/`.

## What it assumes

- Deterministic: one return assumption per period, applied every year. No volatility, no sequence-of-returns risk.
- Pre-tax. Income taxes, OAS clawback, GIS, RRIF minimums, and fees are not modelled.
- Income target is 100% of current income, adjusted for inflation.
- Pensions are fixed nominal payments from retirement.
- CPP/OAS use reference maximums ($18,092 / $8,908 for 2026), adjusted for start age and indexed with inflation. Update them in `src/model.ts` (`GOVERNMENT`) as new figures are published.

The full product rules are in [docs/specification.md](docs/specification.md).

## What it is not

Financial advice. Values are estimates, not guarantees.
