"""Independent hand-calculated cases, rather than tests that copy the algorithm."""

from dataclasses import replace
from datetime import date
import math
import unittest

from indexation import annual_factor, indexed_amount, todays_dollars
from inputs import ACCOUNTS, Account, GOVERNMENT, Person, Scenario, scenario_from_dict, validate
from projection import benefit, birthday_fraction, project
from reporting import annual_table

AS_OF = date(2026, 10, 8)


def blank_person(dob: str = "1961-01-01") -> Person:
    return Person(date.fromisoformat(dob), 65, date(2035, 12, 31),
                  0, 0, 0, 65, 0, 0, {name: Account(0, 0) for name in ACCOUNTS})


def blank_scenario() -> Scenario:
    return Scenario(blank_person(), None, 0, 0, 0)


def account_person(person: Person, name: str = "Cash", **changes) -> Person:
    accounts = dict(person.accounts)
    accounts[name] = replace(accounts[name], **changes)
    return replace(person, accounts=accounts)


class IndexationTests(unittest.TestCase):
    def test_percent_and_initial_year(self):
        self.assertEqual(indexed_amount(1000, 2.5, 0), 1000)
        self.assertAlmostEqual(indexed_amount(1000, 2.5, 1), 1025)
        self.assertAlmostEqual(indexed_amount(1000, 2.5, 2), 1050.625)
        self.assertEqual(indexed_amount(1000, 0, 40), 1000)

    def test_separate_inflation_and_negative_rates(self):
        self.assertAlmostEqual(todays_dollars(indexed_amount(1000, 5, 1), 2, 1), 1050 / 1.02)
        self.assertEqual(indexed_amount(1000, -100, 0), 1000)
        self.assertEqual(indexed_amount(1000, -100, 1), 0)
        self.assertEqual(indexed_amount(1000, -10, 1), 900)
        with self.assertRaises(ValueError):
            annual_factor(1e308, 120)


class ProjectionTests(unittest.TestCase):
    def test_contribute_then_grow_stop_at_retirement(self):
        person = replace(blank_person("1986-01-01"), retirement_age=42)
        person = account_person(person, balance=100, contribution=100)
        p = project(Scenario(person, None, 10, 10, 0), AS_OF)
        self.assertAlmostEqual(p.rows[0].total, 220)
        self.assertAlmostEqual(p.rows[1].total, 352)
        self.assertEqual(p.rows[2].contributions, 0)
        self.assertAlmostEqual(p.savings_at_retirement, 352)
        self.assertAlmostEqual(p.rows[2].total, 387.2)

    def test_numeric_indexation_and_today_values(self):
        person = replace(blank_person("1986-01-01"), retirement_age=43)
        person = account_person(person, contribution=100, indexation_percent=2.5)
        p = project(Scenario(person, None, 0, 0, 2), AS_OF)
        self.assertEqual(p.rows[0].contributions, 100)
        self.assertAlmostEqual(p.rows[1].contributions, 102.5)
        self.assertAlmostEqual(p.rows[2].contributions, 105.0625)
        table = annual_table(p, Scenario(person, None, 0, 0, 2))
        self.assertAlmostEqual(table[1]["contributions_today_cad"], 102.5 / 1.02)

    def test_withdraw_before_growth_custom_order(self):
        person = account_person(replace(blank_person(), income=50), balance=100)
        person = account_person(person, "TFSA", balance=100)
        p = project(Scenario(person, None, 0, 10, 0, ("TFSA", "Cash", "RRSP")), AS_OF)
        self.assertAlmostEqual(p.rows[0].balances["Cash"], 110)
        self.assertAlmostEqual(p.rows[0].balances["TFSA"], 55)
        self.assertEqual(p.rows[0].draw, 50)

    def test_partial_retirement_and_proportional_withdrawal(self):
        client = account_person(replace(blank_person(), income=50), balance=300)
        spouse = account_person(replace(blank_person("1966-01-01"), income=50), balance=100)
        row = project(Scenario(client, spouse, 100, 0, 0), AS_OF).rows[0]
        self.assertEqual(row.need, 100)
        self.assertEqual(row.employment, 50)
        self.assertEqual(row.draw, 50)
        self.assertAlmostEqual(row.total, 437.5)  # 262.5 + 87.5 × 2.

    def test_depletion_and_return_loss(self):
        client = account_person(replace(blank_person(), income=20), balance=100)
        p = project(Scenario(client, None, 0, -20, 0), AS_OF)
        self.assertEqual(p.rows[0].total, 64)
        self.assertEqual(p.first_shortfall.year, 2029)
        self.assertAlmostEqual(p.first_shortfall.shortage, 20 - 12.16)
        self.assertTrue(all(r.total >= 0 for r in p.rows))

    def test_transfer_and_endpoint_year(self):
        client = account_person(replace(blank_person(), income=10, pension=10,
                                        plan_end=date(2027, 6, 30)), balance=100)
        spouse = replace(blank_person("1966-01-01"), income=20, plan_end=date(2033, 12, 31))
        p = project(Scenario(client, spouse, 10, 0, 0), AS_OF)
        self.assertEqual(p.rows[1].need, 30)
        self.assertEqual(p.rows[2].need, 20)
        self.assertEqual(p.rows[2].ages[0], None)
        self.assertEqual(p.rows[2].pension, 0)
        self.assertAlmostEqual(p.rows[2].total, 110)

    def test_shortage_can_be_followed_by_funded_year(self):
        client = replace(blank_person("1962-01-01"), retirement_age=64, income=1000, cpp_percent=100)
        p = project(Scenario(client, None, 0, 0, 0), AS_OF)
        self.assertEqual(p.first_shortfall.year, 2026)
        self.assertEqual(p.funded_years, p.retirement_years_count - 1)
        self.assertEqual(p.rows[1].shortage, 0)

    def test_pre_retirement_income_is_not_saved_and_no_assets_required(self):
        client = replace(blank_person(), income=100, pension=100)
        p = project(Scenario(client, None, 0, 0, 0), AS_OF)
        self.assertIsNone(p.first_shortfall)
        self.assertEqual(p.final_balance, 0)
        client = replace(client, retirement_age=70, income=100000, cpp_percent=100)
        row = project(Scenario(client, None, 0, 0, 0), AS_OF).rows[0]
        self.assertEqual(row.cpp, GOVERNMENT.cpp_annual_maximum)
        self.assertEqual(row.total, 0)

    def test_annual_reconciliation(self):
        client = account_person(replace(blank_person(), income=73), balance=523)
        spouse = account_person(replace(blank_person("1966-01-01"), income=200),
                                balance=811, contribution=131, indexation_percent=2.5)
        p = project(Scenario(client, spouse, 6, 4, 2), AS_OF)
        previous = p.starting_savings
        for row in p.rows:
            self.assertAlmostEqual(sum(row.opening_balances.values()), previous)
            for name in ACCOUNTS:
                surplus = (max(0, row.employment + row.pension + row.cpp + row.oas - row.need)
                           if row.retired and name == 'Cash' else 0)
                self.assertAlmostEqual(row.balances[name], row.opening_balances[name]
                    + row.contributions_by_account[name] - row.withdrawals_by_account[name]
                    + surplus + row.investment_returns[name])
            if row.retired:
                gap = max(0, row.need - row.employment - row.pension - row.cpp - row.oas)
                self.assertAlmostEqual(gap, row.draw + row.raw_shortage)
            previous = row.total

    def test_full_current_year_and_new_base_year(self):
        client = replace(blank_person(), income=100, pension=50)
        s = Scenario(client, None, 0, 0, 5)
        early = project(s, date(2028, 1, 1))
        late = project(s, date(2028, 12, 31))
        self.assertEqual(early, late)
        self.assertEqual(early.rows[0].need, 100)
        self.assertEqual(early.rows[1].need, 105)
        self.assertEqual(early.rows[1].pension, 50)

    def test_tiny_shortfall_preserved_but_exposed(self):
        p = project(Scenario(replace(blank_person(), income=5e-7), None, 0, 0, 0), AS_OF)
        self.assertEqual(p.rows[0].shortage, 0)
        self.assertEqual(p.rows[0].raw_shortage, 5e-7)


class BenefitTests(unittest.TestCase):
    def test_exact_calendar_days(self):
        for dob, year, expected in (("1961-12-31", 2026, 1 / 365),
                                    ("1959-06-30", 2024, 185 / 366),
                                    ("1960-02-29", 2025, 307 / 365)):
            self.assertAlmostEqual(birthday_fraction(date.fromisoformat(dob), 65, year), expected)

    def test_adjustments_reference_year_and_stop(self):
        person = replace(blank_person("1956-01-01"), cpp_percent=100, oas_percent=100)
        self.assertAlmostEqual(benefit(replace(person, cpp_age=60), "cpp", 2026, 0), 18092 * .64)
        self.assertAlmostEqual(benefit(replace(person, cpp_age=70), "cpp", 2026, 0), 18092 * 1.42)
        self.assertAlmostEqual(benefit(replace(person, oas_deferral=5), "oas", 2026, 0), 8908 * 1.36)
        self.assertAlmostEqual(benefit(person, "cpp", 2028, 2), 18092 * 1.02 ** 2)
        self.assertEqual(benefit(person, "cpp", 2036, 2), 0)


class ValidationTests(unittest.TestCase):
    def test_json_schema_and_impossible_dates(self):
        import json
        from pathlib import Path
        data = json.loads((Path(__file__).resolve().parents[1] / "examples/fictional.json").read_text())
        self.assertIsInstance(scenario_from_dict(data), Scenario)
        for patch in ({"typo_inflation": 2}, {"client": {**data["client"], "dob": "2026-02-30"}}):
            with self.subTest(patch=patch), self.assertRaises(ValueError):
                scenario_from_dict({**data, **patch})

    def test_invalid_numeric_inputs(self):
        for value in (math.nan, math.inf, -1, True, "100"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                validate(replace(blank_scenario(), client=replace(blank_person(), income=value)), AS_OF)
        for changes in ({"inflation_percent": -100}, {"before_return_percent": -101},
                        {"withdrawal_order": ("Cash", "Cash", "TFSA")}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                project(replace(blank_scenario(), **changes), AS_OF)

    def test_invalid_dates_accounts_benefits_and_rates(self):
        for changes in ({"dob": date(2027, 1, 1)}, {"plan_end": date(2026, 12, 31)},
                        {"cpp_age": 59}, {"oas_deferral": 1.5}, {"accounts": {}},
                        {"retirement_age": 64.5}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                project(replace(blank_scenario(), client=replace(blank_person(), **changes)), AS_OF)
        for rate in (-101, math.nan, math.inf):
            with self.subTest(rate=rate), self.assertRaises(ValueError):
                project(replace(blank_scenario(), client=account_person(blank_person(),
                             indexation_percent=rate)), AS_OF)


if __name__ == "__main__":
    unittest.main()
