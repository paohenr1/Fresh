"""Run Python and the recovered TypeScript source against matching scenarios."""

from dataclasses import asdict, replace
from datetime import date
import hashlib
import json
import math
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from inputs import ACCOUNTS, Scenario, scenario_from_dict
from projection import project
from tests.test_calculations import AS_OF, account_person, blank_person, blank_scenario


def reference_scenario(s: Scenario) -> dict:
    """Map Python fields to original inputs; only 0/inflation has legacy parity."""
    def person(p):
        return {
            "dob": p.dob.isoformat(), "retirementAge": p.retirement_age,
            "planEnd": p.plan_end.isoformat(), "income": p.income, "pension": p.pension,
            "cppPercent": p.cpp_percent, "cppAge": p.cpp_age,
            "oasPercent": p.oas_percent, "oasDeferral": p.oas_deferral,
            "accounts": {name: {"balance": a.balance, "contribution": a.contribution,
                        "indexed": a.indexation_percent != 0,
                        "indexationPercent": a.indexation_percent} for name, a in p.accounts.items()},
        }
    return {"client": person(s.client), "spouse": person(s.spouse or blank_person()),
            "hasSpouse": s.spouse is not None, "beforeReturn": s.before_return_percent,
            "retirementReturn": s.retirement_return_percent, "inflation": s.inflation_percent,
            "order": list(s.withdrawal_order)}


def source_output(p) -> dict:
    """Select all original output fields, excluding added Python audit fields."""
    def row(r):
        d = asdict(r)
        return {key: d[key] for key in ("year", "ages", "retired", "need", "employment",
                   "cpp", "oas", "pension", "draw", "shortage", "contributions", "balances", "total")}
    return {
        "rows": [row(r) for r in p.rows], "startYear": p.start_year, "endYear": p.end_year,
        "retirementYears": list(p.retirement_years), "firstRetirementYear": p.first_retirement_year,
        "savingsAtRetirement": p.savings_at_retirement, "startingSavings": p.starting_savings,
        "finalBalance": p.final_balance, "firstTarget": p.first_target,
        "fundedYears": p.funded_years, "retirementYearsCount": p.retirement_years_count,
        "alreadyRetired": p.already_retired,
        **({"firstShortfall": row(p.first_shortfall)} if p.first_shortfall else {}),
    }


def cases():
    base = blank_scenario()
    working = replace(blank_person("1986-01-01"), retirement_age=42, income=100)
    zero = replace(base, client=account_person(working, balance=100, contribution=100),
                   before_return_percent=10, retirement_return_percent=10)
    yield "zero indexation and retirement timing", zero, AS_OF, False
    yield "inflation-linked contributions", replace(zero, inflation_percent=2,
        client=account_person(zero.client, "RRSP", contribution=100, indexation_percent=2)), AS_OF, False
    yield "zero returns and depletion", replace(base,
        client=account_person(replace(base.client, income=60), balance=100)), AS_OF, False
    yield "negative returns", replace(base, retirement_return_percent=-20,
        client=account_person(replace(base.client, income=20), balance=100)), AS_OF, False
    yield "custom withdrawal order", replace(base, retirement_return_percent=10,
        client=account_person(account_person(replace(base.client, income=50), balance=100),
                              "TFSA", balance=100), withdrawal_order=("TFSA", "Cash", "RRSP")), AS_OF, False
    client = account_person(replace(base.client, income=50), balance=300)
    spouse = account_person(replace(blank_person("1966-01-01"), income=50), balance=100)
    yield "partial retirement pro rata returns", Scenario(client, spouse, 100, 0, 0), AS_OF, False
    yield "survivor transfer", Scenario(replace(client, plan_end=date(2027, 6, 30), pension=50),
        replace(spouse, income=20, plan_end=date(2033, 12, 31)), 10, 0, 0), AS_OF, False
    yield "birthday benefits and inflation", replace(base, inflation_percent=2,
        client=replace(base.client, dob=date(1961, 6, 15), cpp_percent=100, oas_percent=100)), AS_OF, False
    yield "leap birthday", replace(base, client=replace(base.client, dob=date(1960, 2, 29),
        cpp_percent=100, oas_percent=100)), date(2025, 10, 8), False
    yield "later projection baseline", replace(base, inflation_percent=5,
        client=replace(base.client, income=100, pension=50, cpp_percent=100)), date(2028, 10, 1), False
    yield "shortage then funded years", replace(base, client=replace(base.client, dob=date(1962, 1, 1),
        retirement_age=64, income=1000, cpp_percent=100)), AS_OF, False
    yield "tiny shortfall threshold", replace(base, client=replace(base.client, income=5e-7)), AS_OF, False
    for age, deferral in ((60, 0), (70, 5)):
        yield f"CPP age {age} OAS deferral {deferral}", replace(base, client=replace(base.client,
            dob=date(1956, 1, 1), cpp_age=age, oas_deferral=deferral,
            cpp_percent=100, oas_percent=100)), AS_OF, False
    yield "funded with zero savings", replace(base, client=replace(base.client, income=100, pension=100)), AS_OF, False
    # Reproduce the actual application's default example over its full horizon.
    from inputs import Account
    def default_person(age, income):
        return replace(blank_person(f"{2026 - age}-06-15"),
            plan_end=date(2026 + 95 - age, 12, 31), income=income, pension=18000,
            cpp_percent=100, oas_percent=100,
            accounts={"Cash": Account(25000, 2000), "RRSP": Account(220000, 12000),
                      "TFSA": Account(90000, 6000)})
    default = Scenario(default_person(45, 65000), None, 6, 4, 2)
    yield "original default 51-year single-person example", default, AS_OF, False
    yield "original default 54-year spouse example", replace(default,
          spouse=default_person(42, 55000)), AS_OF, False
    data = json.loads((ROOT / "examples/fictional.json").read_text())
    fictional = scenario_from_dict(data)
    # Flat version can compare directly with the original source.
    def flat(p):
        return replace(p, accounts={name: replace(a, indexation_percent=0) for name, a in p.accounts.items()})
    yield "fictional household flat", replace(fictional, client=flat(fictional.client),
          spouse=flat(fictional.spouse)), AS_OF, False
    yield "fictional household independent rates", fictional, AS_OF, True
    for rate in (2.5, -10, -100, 125):
        yield f"numeric indexation {rate}% versus 2% inflation", replace(zero, inflation_percent=2,
            client=account_person(zero.client, indexation_percent=rate)), AS_OF, True


def main():
    snapshot = json.loads((ROOT / "SOURCE.json").read_text())
    for relative, expected_hash in snapshot["sha256"].items():
        actual = hashlib.sha256((ROOT / "original_fresh" / relative).read_bytes()).hexdigest()
        assert actual == expected_hash, f"Recovered source changed: {relative}"
    entries = list(cases())
    payload = [{"name": name, "scenario": reference_scenario(s), "as_of": as_of.isoformat(),
                "numeric": numeric} for name, s, as_of, numeric in entries]
    completed = subprocess.run(["node", str(ROOT / "tests/reference_runner.mjs")],
        input=json.dumps(payload), text=True, capture_output=True, check=True)
    reference = json.loads(completed.stdout)
    report = []
    for (name, s, as_of, numeric), original in zip(entries, reference, strict=True):
        maximum_difference = 0.0
        number_count = 0

        def compare(a, b, path="projection"):
            nonlocal maximum_difference, number_count
            if isinstance(a, dict):
                assert set(a) == set(b), (path, set(a), set(b))
                for key in a:
                    compare(a[key], b[key], f"{path}.{key}")
            elif isinstance(a, (tuple, list)):
                assert len(a) == len(b), path
                for i, (x, y) in enumerate(zip(a, b, strict=True)):
                    compare(x, y, f"{path}[{i}]")
            elif isinstance(a, (int, float)) and not isinstance(a, bool):
                number_count += 1
                maximum_difference = max(maximum_difference, abs(a - b))
                assert math.isclose(a, b, rel_tol=1e-12, abs_tol=1e-8), (path, a, b)
            else:
                assert a == b, (path, a, b)

        projection = project(s, as_of)
        compare(source_output(projection), original["projection"])
        for row in projection.rows:
            for account in ACCOUNTS:
                expected = (row.opening_balances[account] + row.contributions_by_account[account]
                            - row.withdrawals_by_account[account] + row.investment_returns[account])
                if row.retired and account == 'Cash':
                    expected += max(0.0, row.employment + row.pension + row.cpp + row.oas - row.need)
                assert math.isclose(expected, row.balances[account], rel_tol=1e-12, abs_tol=1e-8)
        reference_label = "single-formula indexation extension" if numeric else "untouched original TypeScript"
        if original['surplus_saving']:
            reference_label += "; approved surplus-saving extension"
        report.append({"case": name, "reference": reference_label,
                       "intentional_surplus_saving": original['surplus_saving'],
                       "legacy_final_balance_difference_cad": original['legacy_final_balance_difference_cad'],
                       "annual_rows": len(projection.rows), "numeric_values_compared": number_count,
                       "maximum_absolute_difference_cad": maximum_difference, "result": "PASS"})
    result = {"source_commit": snapshot["commit"],
              "tolerance": {"relative": 1e-12, "absolute_cad": 1e-8}, "cases": report}
    (ROOT / "verification_results.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
