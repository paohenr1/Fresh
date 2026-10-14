"""FRESH's annual deterministic, gross pre-tax retirement calculations."""

import calendar
from dataclasses import dataclass, field
from datetime import date
import math

from indexation import annual_factor, indexed_amount
from inputs import ACCOUNTS, GOVERNMENT, GovernmentReferences, Person, Scenario, validate


@dataclass(frozen=True)
class AnnualRow:
    year: int
    ages: tuple[int | None, ...]
    retired: bool
    need: float
    employment: float
    cpp: float
    oas: float
    pension: float
    draw: float
    shortage: float
    raw_shortage: float
    contributions: float
    opening_balances: dict[str, float]
    contributions_by_account: dict[str, float]
    withdrawals_by_account: dict[str, float]
    investment_returns: dict[str, float]
    balances: dict[str, float]
    total: float


@dataclass(frozen=True)
class Projection:
    rows: list[AnnualRow]
    start_year: int
    end_year: int
    retirement_years: tuple[int, ...]
    first_retirement_year: int
    savings_at_retirement: float
    starting_savings: float
    final_balance: float
    first_target: float
    funded_years: int
    retirement_years_count: int
    first_shortfall: AnnualRow | None
    already_retired: bool
    # Exact date is display metadata; financial projections remain annual.
    as_of: date = field(compare=False)


def birthday_fraction(dob: date, age: int, year: int) -> float:
    """First benefit year: days from birthday inclusive / days in calendar year."""
    start_year = dob.year + age
    if year < start_year:
        return 0.0
    if year > start_year:
        return 1.0
    day = 28 if dob.month == 2 and dob.day == 29 and not calendar.isleap(year) else dob.day
    birthday = date(year, dob.month, day)
    year_end = date(year + 1, 1, 1)
    return (year_end - birthday).days / (year_end - date(year, 1, 1)).days


def benefit(person: Person, kind: str, year: int, inflation_percent: float,
            government: GovernmentReferences = GOVERNMENT) -> float:
    """Reference maximum × entitlement × start adjustment × inflation × proration."""
    if kind not in ("cpp", "oas"):
        raise ValueError("Benefit kind must be cpp or oas")
    if year > person.plan_end.year:
        return 0.0
    if kind == "cpp":
        age = person.cpp_age
        adjustment = min(1.42, max(0.64, 1 + (age - 65) * 12
                                   * (0.006 if age < 65 else 0.007)))
        maximum, percent = government.cpp_annual_maximum, person.cpp_percent
    else:
        age = 65 + person.oas_deferral
        adjustment = 1 + person.oas_deferral * 12 * 0.006
        maximum, percent = government.oas_annual_maximum, person.oas_percent
    # Preserve source operation order; the base year differs from current inputs.
    return (maximum * percent / 100 * adjustment
            * annual_factor(inflation_percent, year - government.reference_year)
            * birthday_fraction(person.dob, age, year))


def project(scenario: Scenario, as_of: date) -> Projection:
    """Project full calendar years, including the current and final plan years."""
    validate(scenario, as_of)
    people = scenario.people
    start_year = as_of.year
    retirement_years = tuple(p.retirement_year for p in people)
    first_retirement_year = min(retirement_years)
    end_year = max(p.plan_end.year for p in people)
    # Separate owners matter: their return regimes can differ in the same year.
    balances = [{name: p.accounts[name].balance for name in ACCOUNTS} for p in people]

    def totals() -> dict[str, float]:
        return {name: sum(b[name] for b in balances) for name in ACCOUNTS}

    starting_savings = sum(totals().values())
    savings_at_retirement = starting_savings
    first_target = 0.0
    rows: list[AnnualRow] = []
    for year in range(start_year, end_year + 1):
        active = [year <= p.plan_end.year for p in people]
        opening = totals()
        # Transfer existing assets before cash flows in the year after a plan ends.
        # Household opening totals are conserved; survivor's rate applies thereafter.
        if len(people) == 2:
            for i in range(2):
                if not active[i] and active[1 - i]:
                    for name in ACCOUNTS:
                        balances[1 - i][name] += balances[i][name]
                        balances[i][name] = 0.0
        retired = year >= first_retirement_year
        if year == max(start_year, first_retirement_year):
            savings_at_retirement = sum(totals().values())

        # Step 1: working owners contribute at the beginning of the year.
        # Each item's own rate replaces the source's binary inflation option.
        elapsed = year - start_year
        inflation_factor = annual_factor(scenario.inflation_percent, elapsed)
        added = dict.fromkeys(ACCOUNTS, 0.0)
        contributions = 0.0
        for i, person in enumerate(people):
            if active[i] and year < retirement_years[i]:
                for name in ACCOUNTS:
                    account = person.accounts[name]
                    amount = indexed_amount(account.contribution, account.indexation_percent, elapsed)
                    balances[i][name] += amount
                    added[name] += amount
                    contributions += amount

        # Step 2: target is 100% of active people's original current incomes.
        # Working income counts during partial retirement; no surplus is reinvested.
        need = sum(p.income * inflation_factor for i, p in enumerate(people)
                   if active[i]) if retired else 0.0
        employment = sum(p.income * inflation_factor for i, p in enumerate(people)
                         if active[i] and year < retirement_years[i])
        # The entered pension is payable in its retirement year (t=0).
        # Already-retired owners retain that retirement-year base; rates are %.
        pension = sum(indexed_amount(p.pension, p.pension_indexation_percent,
                                     year - retirement_years[i])
                      for i, p in enumerate(people)
                      if active[i] and year >= retirement_years[i])
        cpp = sum(benefit(p, "cpp", year, scenario.inflation_percent) for p in people)
        oas = sum(benefit(p, "oas", year, scenario.inflation_percent) for p in people)
        remaining = max(0.0, need - employment - pension - cpp - oas) if retired else 0.0

        # Step 3: ordered household draws, allocated pro rata within each type.
        # Contributions are already available, including a working spouse's.
        withdrawn = dict.fromkeys(ACCOUNTS, 0.0)
        draw = 0.0
        for name in scenario.withdrawal_order:
            available = sum(b[name] for b in balances)
            withdrawal = min(remaining, available)
            if available > 0:
                for balance in balances:
                    balance[name] = max(0.0, balance[name] - withdrawal * balance[name] / available)
            remaining = max(0.0, remaining - withdrawal)
            withdrawn[name] = withdrawal
            draw += withdrawal

        # Step 4: grow each owner's remaining balances at their applicable rate.
        # Multiplication matches source order; returns are an added audit column.
        returns = dict.fromkeys(ACCOUNTS, 0.0)
        for i in range(len(people)):
            rate = (scenario.before_return_percent if year < retirement_years[i]
                    else scenario.retirement_return_percent)
            for name in ACCOUNTS:
                before_growth = balances[i][name]
                balances[i][name] *= 1 + rate / 100
                returns[name] += balances[i][name] - before_growth
        closing = totals()
        # Source's tiny-shortfall convention is preserved, with the raw remainder
        # exposed separately so audit users can see what was suppressed.
        row = AnnualRow(
            year=year,
            ages=tuple(year - p.dob.year if active[i] else None for i, p in enumerate(people)),
            retired=retired, need=need, employment=employment,
            cpp=cpp, oas=oas, pension=pension, draw=draw,
            shortage=0.0 if remaining < 0.000001 else remaining,
            raw_shortage=remaining, contributions=contributions,
            opening_balances=opening, contributions_by_account=added,
            withdrawals_by_account=withdrawn, investment_returns=returns,
            balances=closing, total=sum(closing.values()),
        )
        values = [need, employment, pension, cpp, oas, contributions, draw, remaining,
                  *opening.values(), *added.values(), *withdrawn.values(),
                  *returns.values(), *closing.values(), row.total]
        if not all(math.isfinite(value) for value in values):
            raise ValueError(f"Projection exceeds numeric capacity in year {year}")
        if year == max(start_year, first_retirement_year):
            first_target = need
        rows.append(row)
    retirement_rows = [row for row in rows if row.retired]
    return Projection(
        rows=rows, start_year=start_year, end_year=end_year,
        retirement_years=retirement_years, first_retirement_year=first_retirement_year,
        savings_at_retirement=savings_at_retirement, starting_savings=starting_savings,
        final_balance=rows[-1].total, first_target=first_target,
        funded_years=sum(row.shortage == 0 for row in retirement_rows),
        retirement_years_count=len(retirement_rows),
        first_shortfall=next((row for row in retirement_rows if row.shortage > 0), None),
        already_retired=first_retirement_year < start_year,
        as_of=as_of,
    )
