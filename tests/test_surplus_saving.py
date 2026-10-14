"""Independent examples for the approved retirement-income surplus rule."""

from dataclasses import fields, replace
import unittest

from projection import AnnualRow, project
from inputs import GOVERNMENT
from tests.test_calculations import AS_OF, account_person, blank_person, blank_scenario


class SurplusSavingTests(unittest.TestCase):
    def test_surplus_enters_cash_before_growth_and_is_not_a_contribution(self):
        person = replace(blank_person(), income=100, pension=120)
        s = replace(blank_scenario(), client=person, retirement_return_percent=10)
        p = project(s, AS_OF)
        self.assertEqual(p.rows[0].contributions, 0)
        self.assertEqual(p.rows[0].draw, 0)
        self.assertAlmostEqual(p.rows[0].balances['Cash'], 22)
        self.assertAlmostEqual(p.rows[0].investment_returns['Cash'], 2)
        self.assertAlmostEqual(p.rows[1].balances['Cash'], 46.2)
        self.assertEqual(p.savings_at_retirement, 0)  # Opening amount stays opening.
        self.assertTrue(all(r.balances['RRSP'] == r.balances['TFSA'] == 0 for r in p.rows))
        self.assertFalse(any('surplus' in field.name for field in fields(AnnualRow)))

    def test_saved_surplus_funds_a_later_gap_and_then_depletes(self):
        person = replace(blank_person(), income=100, pension=150,
                         pension_indexation_percent=-50)
        p = project(replace(blank_scenario(), client=person), AS_OF)
        self.assertEqual(p.rows[0].balances['Cash'], 50)
        self.assertEqual(p.rows[1].draw, 25)
        self.assertEqual(p.rows[1].balances['Cash'], 25)
        self.assertEqual(p.rows[2].draw, 25)
        self.assertEqual(p.rows[2].shortage, 37.5)
        self.assertEqual(p.rows[2].total, 0)

    def test_pre_retirement_income_is_not_automatically_saved(self):
        person = replace(blank_person(), retirement_age=70, income=100,
                         cpp_percent=100, cpp_age=60)
        p = project(replace(blank_scenario(), client=person), AS_OF)
        self.assertGreater(p.rows[0].cpp + p.rows[0].employment, 100)
        self.assertFalse(p.rows[0].retired)
        self.assertEqual(p.rows[0].total, 0)

    def test_zero_surplus_preserves_withdrawals_and_return_timing(self):
        person = account_person(replace(blank_person(), income=100, pension=50), balance=100)
        p = project(replace(blank_scenario(), client=person, retirement_return_percent=10), AS_OF)
        self.assertEqual(p.rows[0].draw, 50)
        self.assertAlmostEqual(p.rows[0].balances['Cash'], 55)
        self.assertAlmostEqual(p.rows[1].balances['Cash'], 5.5)

    def test_both_retired_and_survivor_income_endpoints(self):
        from datetime import date
        client = replace(blank_person(), income=100, pension=130,
                         plan_end=date(2027, 12, 31))
        spouse = replace(blank_person(), income=50, pension=60)
        s = replace(blank_scenario(), client=client, spouse=spouse)
        p = project(s, AS_OF)
        self.assertEqual(p.rows[0].total, 40)
        self.assertEqual(p.rows[1].total, 80)
        self.assertEqual(p.rows[2].need, 50)
        self.assertEqual(p.rows[2].pension, 60)
        self.assertEqual(p.rows[2].total, 90)

    def test_income_can_be_deflated_without_changing_surplus_rule(self):
        person = replace(blank_person(), income=100, pension=120,
                         pension_indexation_percent=5)
        p = project(replace(blank_scenario(), client=person, inflation_percent=2), AS_OF)
        self.assertEqual(p.rows[0].total, 20)
        self.assertAlmostEqual(p.rows[1].total, 44)  # 126 pension - 102 target.

    def test_partial_retirement_allocates_only_net_excess_to_its_earner(self):
        client = replace(blank_person(), income=100, pension=80)
        spouse = replace(blank_person(), retirement_age=70, income=50,
                         cpp_percent=40 / GOVERNMENT.cpp_annual_maximum * 100)
        s = replace(blank_scenario(), client=client, spouse=spouse,
                    before_return_percent=10, retirement_return_percent=4)
        row = project(s, AS_OF).rows[0]
        self.assertEqual(row.need, 150)
        self.assertEqual(row.employment, 50)
        self.assertAlmostEqual(row.cpp, 40)
        # Working spouse's 40 excess first covers retired person's 20 gap.
        # Only the net 20 is saved in working spouse's Cash, then grows by 10%.
        self.assertAlmostEqual(row.balances['Cash'], 22)
        self.assertEqual(row.contributions, 0)
        self.assertEqual(row.draw, 0)

    def test_partial_retirement_positive_excesses_use_each_owners_rate(self):
        client = replace(blank_person(), income=100, pension=130)
        spouse = replace(blank_person(), retirement_age=70, income=50,
                         cpp_percent=10 / GOVERNMENT.cpp_annual_maximum * 100)
        s = replace(blank_scenario(), client=client, spouse=spouse,
                    before_return_percent=10, retirement_return_percent=4)
        row = project(s, AS_OF).rows[0]
        self.assertAlmostEqual(row.balances['Cash'], 30 * 1.04 + 10 * 1.10)

    def test_personal_excess_is_not_saved_while_household_has_a_gap(self):
        client = replace(blank_person(), income=100, pension=80)
        spouse = replace(blank_person(), retirement_age=70, income=50,
                         cpp_percent=10 / GOVERNMENT.cpp_annual_maximum * 100)
        row = project(replace(blank_scenario(), client=client, spouse=spouse), AS_OF).rows[0]
        self.assertAlmostEqual(row.shortage, 10)
        self.assertEqual(row.total, 0)


if __name__ == '__main__':
    unittest.main()
