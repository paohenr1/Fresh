"""Hand-calculated pension timing, independence and compatibility checks."""

from copy import deepcopy
from dataclasses import replace
from datetime import date
import json
import math
from pathlib import Path
import unittest

from inputs import scenario_from_dict
from projection import project
from reporting import annual_table, render_html


class PensionIndexationTests(unittest.TestCase):
    def setUp(self):
        self.data = json.loads((Path(__file__).parents[1] / 'examples/fictional.json').read_text())
        self.data['spouse'] = None
        self.data['client'].update(dob='1963-01-01', retirement_age=65,
                                   plan_end='2033-12-31', pension=1000,
                                   pension_indexation_percent=2.5)
        self.scenario = scenario_from_dict(self.data)
        self.start = date.fromisoformat(self.data['as_of'])

    def test_retirement_year_no_immediate_increase_and_real_values(self):
        projection = project(self.scenario, self.start)
        self.assertEqual([r.pension for r in projection.rows[:3]], [0, 0, 1000])
        self.assertAlmostEqual(projection.rows[3].pension, 1025)
        self.assertAlmostEqual(projection.rows[4].pension, 1050.625)
        table = annual_table(projection, self.scenario)
        self.assertAlmostEqual(table[3]['pension_income_today_cad'], 1025 / 1.02 ** 3)

    def test_already_retired_and_minus_100_percent(self):
        person = replace(self.scenario.client, dob=date(1960, 1, 1))
        p = project(replace(self.scenario, client=person), self.start)
        self.assertAlmostEqual(p.rows[0].pension, 1025)  # Retired in 2025.
        person = replace(self.scenario.client, pension_indexation_percent=-100)
        p = project(replace(self.scenario, client=person), self.start)
        self.assertEqual(p.rows[2].pension, 1000)
        self.assertEqual(p.rows[3].pension, 0)

    def test_legacy_inputs_and_zero_rate_preserve_results(self):
        legacy = deepcopy(self.data)
        del legacy['client']['pension_indexation_percent']
        flat = deepcopy(legacy)
        flat['client']['pension_indexation_percent'] = 0
        self.assertEqual(project(scenario_from_dict(legacy), self.start),
                         project(scenario_from_dict(flat), self.start))

    def test_people_have_independent_rates_and_stop_at_plan_end(self):
        client = replace(self.scenario.client, plan_end=date(2029, 12, 31))
        spouse = replace(client, pension=2000, pension_indexation_percent=5,
                         plan_end=date(2033, 12, 31))
        p = project(replace(self.scenario, client=client, spouse=spouse), self.start)
        self.assertEqual(p.rows[2].pension, 3000)
        self.assertAlmostEqual(p.rows[3].pension, 3125)
        self.assertAlmostEqual(p.rows[4].pension, 2205)  # Client payments ended.

    def test_invalid_rates(self):
        for rate in (-100.1, math.nan, math.inf, True, None, '2.5'):
            with self.subTest(rate=rate), self.assertRaises(ValueError):
                project(replace(self.scenario, client=replace(self.scenario.client,
                    pension_indexation_percent=rate)), self.start)

    def test_indexed_pension_changes_draws_and_balances_with_zero_returns(self):
        person = replace(self.scenario.client, income=2000, pension_indexation_percent=10,
                         cpp_percent=0, oas_percent=0)
        s = replace(self.scenario, client=person, before_return_percent=0,
                    retirement_return_percent=0, inflation_percent=0)
        p = project(s, self.start)
        self.assertEqual(p.rows[2].draw, 1000)
        self.assertEqual(p.rows[3].draw, 900)
        for row in p.rows:
            self.assertAlmostEqual(row.total, sum(row.opening_balances.values())
                                   + row.contributions - row.draw)

    def test_collapsed_editors_preserve_rates(self):
        html = render_html(project(self.scenario, self.start), self.scenario, live_inputs=self.data)
        self.assertIn('<details class="date-edit indexation-edit">', html)
        self.assertIn('Edit indexation · 2.5%/year', html)
        self.assertIn('data-input="client.pension_indexation_percent"', html)
        self.assertNotIn('Stays fixed; no inflation indexing', html)


if __name__ == '__main__':
    unittest.main()
