"""Compare the published browser engine with Python, including audit balances.

No npm install is required for this check: Node strips TypeScript annotations
from the same model.ts file compiled into the deployed website.
"""

from dataclasses import replace
from datetime import date
import json
import math
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from inputs import scenario_from_dict
from projection import project
from tests.verify_original import cases, reference_scenario, source_output
from tests.test_calculations import blank_person, blank_scenario
from inputs import GOVERNMENT


def main():
    """Require financial agreement to 1e-8 CAD absolute or 1e-12 relative."""
    scenarios = [(name, scenario, on) for name, scenario, on, _ in cases()]
    data = json.loads((ROOT / 'examples/fictional.json').read_text())
    base = scenario_from_dict(data)
    client = replace(blank_person(), income=100, pension=80)
    spouse = replace(blank_person(), retirement_age=70, income=50,
                     cpp_percent=40 / GOVERNMENT.cpp_annual_maximum * 100)
    partial = replace(blank_scenario(), client=client, spouse=spouse,
                      before_return_percent=10, retirement_return_percent=4)
    scenarios.extend([
        ('partial retirement surplus from working spouse CPP',partial,date(2026,10,8)),
        ('partial retirement multiple positive excesses',replace(partial,
            client=replace(client,pension=130),spouse=replace(spouse,
            cpp_percent=10 / GOVERNMENT.cpp_annual_maximum * 100)),date(2026,10,8)),
        ('surplus funds later depletion',replace(blank_scenario(),client=replace(
            blank_person(),income=100,pension=150,pension_indexation_percent=-50)),date(2026,10,8)),
    ])
    for rate in (0, 2.5, -10, -100, 125):
        for already_retired in (False, True):
            person = replace(base.client, dob=date(1959 if already_retired else 1963, 6, 15),
                             pension_indexation_percent=rate)
            scenarios.append((f'pension {rate}% already retired {already_retired}',
                              replace(base, client=person, spouse=replace(base.spouse,
                                  pension_indexation_percent=5)), date(2026, 10, 8)))
    inputs = []
    for _, scenario, on in scenarios:
        record = reference_scenario(scenario)
        record['asOf'] = on.isoformat()
        for key, person in [('client', scenario.client), ('spouse', scenario.spouse)]:
            record[key]['pensionIndexationPercent'] = person.pension_indexation_percent if person else 0
            for account in record[key]['accounts'].values():
                account.pop('indexed', None)
        inputs.append(record)
    script = """
      import fs from 'node:fs';
      const {project} = await import(process.argv[1]);
      const inputs = JSON.parse(fs.readFileSync(0,'utf8'));
      process.stdout.write(JSON.stringify(inputs.map(s => project(s))));
    """
    actual = json.loads(subprocess.check_output(['node', '--input-type=module', '--eval', script,
        (ROOT / 'web/src/model.ts').as_uri()], input=json.dumps(inputs).encode()))
    reports = []
    for (name, scenario, on), browser in zip(scenarios, actual, strict=True):
        projection = project(scenario, on)
        expected = source_output(projection)
        for record, row in zip(expected['rows'], projection.rows, strict=True):
            record.update(openingBalances=row.opening_balances,
                          contributionsByAccount=row.contributions_by_account,
                          withdrawalsByAccount=row.withdrawals_by_account,
                          investmentReturns=row.investment_returns, rawShortage=row.raw_shortage)
        # firstShortfall contains a full Row in the browser engine too.
        if 'firstShortfall' in expected:
            expected['firstShortfall'] = next(row for row in expected['rows']
                if row['year'] == projection.first_shortfall.year)
        maximum, count = 0.0, 0
        def compare(a, b, path='projection'):
            nonlocal maximum, count
            if isinstance(a, dict):
                assert set(a) == set(b), (name, path, set(a) ^ set(b))
                for key in a: compare(a[key], b[key], path + '.' + key)
            elif isinstance(a, (list, tuple)):
                assert len(a) == len(b), (name, path)
                for i, (x, y) in enumerate(zip(a, b, strict=True)): compare(x, y, f'{path}[{i}]')
            elif isinstance(a, (float, int)) and not isinstance(a, bool):
                maximum = max(maximum, abs(a-b)); count += 1
                assert math.isclose(a,b,rel_tol=1e-12,abs_tol=1e-8), (name,path,a,b)
            else:
                assert a == b, (name,path,a,b)
        compare(expected,browser)
        reports.append({'case':name,'result':'PASS','numeric_values_compared':count,
                        'maximum_absolute_difference_cad':maximum})
    result = {'reference':'Python projection.py; deployed web/src/model.ts',
              'tolerance':{'relative':1e-12,'absolute_cad':1e-8},'cases':reports}
    (ROOT / 'browser_verification_results.json').write_text(json.dumps(result,indent=2)+'\n')
    print(f'{len(reports)} browser/Python comparisons passed; max difference '
          f'{max(row["maximum_absolute_difference_cad"] for row in reports):.12g} CAD')


if __name__ == '__main__':
    main()
