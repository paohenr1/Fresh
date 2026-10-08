# Fresh

A private, browser-only Canadian retirement projection calculator. Separate
retirement dates, household income during partial retirement, fixed pensions,
CPP/OAS, account balances, charts, and client PDF export are supported.

The agreed product rules are in [docs/specification.md](docs/specification.md).

## Development

Use Node.js 22.12 or newer (this cloud environment uses Node.js 24). From the
existing `/workspace/Fresh` checkout:

```sh
npm ci --cache /workspace/.npm-cache
npm run dev -- --host 0.0.0.0 --port 5173 --strictPort
```

This is a Vite/React/TypeScript application. There is no application backend,
database, authentication, or required secret. The npm registry is required for
dependency installation; the running application uses locally bundled assets.
No financial inputs are sent or saved, and reloading starts a fresh example.

Each cloud task already has an isolated environment. Use its existing checkout;
do not create a Git worktree unless explicitly requested.

## Validation

```sh
npm test
npm run build
npm run test:browser
```

The model tests cover annual timing, indexed contributions, partial retirement,
proportional withdrawals, distinct return regimes, beneficiary assumptions,
CPP/OAS adjustments, exact birthday prorating, and shortfall verdicts. Browser
tests exercise live updates, invalid inputs, spouse controls, mobile layout,
network privacy, and repeat PDF export after changing inputs.

Browser tests use system Chromium at `/usr/bin/chromium`. Elsewhere, set
`CHROMIUM_PATH` to an installed Chromium executable. They start a development
server if one is not already running. Browser tests freeze the date for stable
expectations; normal calculator use takes the browser's current date.

`npm run build` writes the static application to `dist/`. `npm run preview` can
serve that build for local verification. Live development processes must be
restarted in a new task; dependencies and generated files can be retained.

## Publishing with GitHub Pages

The workflow in `.github/workflows/pages.yml` tests, builds, and deploys pushes
to `main`. In the repository's **Settings → Pages**, select **GitHub Actions**
as the build source. The expected website is `https://paohenr1.github.io/Fresh/`.

For this deployment the workflow sets `GITHUB_PAGES=true`, which builds assets
under `/Fresh/`. Local development and ordinary builds keep the root `/` base.
No ZIP download, backend, or deployment API key is required.

## Updating government amounts

Edit the clearly labelled `GOVERNMENT` object in `src/model.ts`: reference year,
CPP annual maximum, and OAS annual maximum. Update the reference year and figures
together. The initial 2026 figures come from the product specification; they
are not fetched live. Benefits are extrapolated using the selected inflation.

## Important assumptions

- Gross, pre-tax amounts with constant annual return assumptions.
- 100% of originally entered current income sets the inflation-adjusted target.
- Employment income counts during partial retirement but is omitted from the
  income chart, as explained beside that chart.
- Only entered contributions are invested; excess income is not automatically
  saved. This is not a full household cash-flow budget.
- Retirement starts in January of the selected age's calendar year; the current
  year is modelled in full. No contribution in a person's retirement year.
- Plan endpoints are treated as year-end. The survivor retains savings and uses
  their own original current income for the target. Legal transfers, estate
  tax, survivor pensions, and CPP survivor benefits are not calculated.
- Pensions stay fixed. CPP/OAS use exact-day birthday prorating in their first
  year; a February 29 birthday uses February 28 in a non-leap start year.
- For someone already retired, the first savings metric reports current
  savings; it does not reconstruct a historical retirement balance.
- PDF export re-runs the current scenario. Summary and charts occupy pages 1–2;
  the complete table continues from page 3 with repeated headings.

Values are estimates, not guarantees. The UI and PDF describe excluded taxes,
clawback, GIS, RRIF/LIF rules, fees, and other limitations.
