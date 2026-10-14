# FRESH browser planner

This is the shareable GitHub Pages version of the Python planner in the parent
folder. Calculation and PDF code run on the visitor's device. No financial
inputs are saved or sent to a backend.

From the repository root:

```text
npm ci --prefix web
npm run dev --prefix web
```

The terminal prints the local browser address. To check and build:

```text
npm test --prefix web
python tests/verify_browser.py
npm run build --prefix web
```

`src/model.ts` keeps related annual calculations together, using percentage
numbers and the same order as Python. `src/example.json` is the fictional Python
example mapped to browser field names; its start date is pinned. Update both
examples deliberately when changing that baseline. `src/App.tsx` is the editable
interface, `src/Charts.tsx` draws area graphs and annual tables, and `src/pdf.ts`
produces both reports from an input snapshot. Whole-dollar display rounds ties
to even, as Python does, while calculations retain full precision.

Once either person retires, net household income above the target enters Cash
before growth. The net surplus is allocated proportionally using positive
personal income excesses over each person's target share; each Cash owner keeps
their existing working/retired return rate. Salary alone cannot create excess,
but CPP/OAS can begin before retirement at their selected ages. Contribution
fields remain entered contributions and no surplus column is added.

`tests/browser.spec.ts` checks hidden indexation, changing values, nominal tables,
invalid inputs, exact-date editors, mobile layout, offline exports and long
projection reports. Run `npm run test:browser --prefix web` using installed Edge
on Windows; CI installs Playwright Chromium on Linux.

Publishing uses the root Pages workflow and its `/Fresh/` base path. It checks
browser/Python agreement before uploading the built static files. Keep the
Python engine and browser engine together when changing formulas; neither
language version automatically updates the other. The reference copy in
`original_fresh/` is immutable and is not the deployed website.
