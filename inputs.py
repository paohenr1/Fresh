"""Input records and validation. Dollar amounts are nominal CAD; rates are percent."""

from dataclasses import dataclass
from datetime import date
import math
from typing import Any

ACCOUNTS = ("Cash", "RRSP", "TFSA")
MAX_INPUT_AMOUNT = 9_007_199_254_740_991  # Original JavaScript safe-integer limit.


@dataclass(frozen=True)
class Account:
    balance: float
    contribution: float
    indexation_percent: float = 0.0


@dataclass(frozen=True)
class Person:
    dob: date
    retirement_age: int
    plan_end: date
    income: float
    pension: float
    cpp_percent: float
    cpp_age: int
    oas_percent: float
    oas_deferral: int
    accounts: dict[str, Account]

    @property
    def retirement_year(self) -> int:
        """Retirement starts January 1 of the year the selected age is attained."""
        return self.dob.year + self.retirement_age


@dataclass(frozen=True)
class Scenario:
    client: Person
    spouse: Person | None
    before_return_percent: float
    retirement_return_percent: float
    inflation_percent: float
    withdrawal_order: tuple[str, ...] = ACCOUNTS

    @property
    def people(self) -> tuple[Person, ...]:
        return (self.client,) if self.spouse is None else (self.client, self.spouse)


@dataclass(frozen=True)
class GovernmentReferences:
    """Fixed source assumptions, not a live tax/benefit rules service."""
    reference_year: int = 2026
    cpp_annual_maximum: float = 18_092.0
    oas_annual_maximum: float = 8_908.0


GOVERNMENT = GovernmentReferences()


def age_on_date(birth: date, on: date) -> int:
    """Completed age for display; the annual model separately uses year-based ages."""
    return on.year - birth.year - ((on.month, on.day) < (birth.month, birth.day))


def validate(scenario: Scenario, as_of: date) -> None:
    """Raise ValueError with field names; accept financial shortfalls as valid."""
    errors: list[str] = []

    def number(key: str, value: float, minimum: float,
               maximum: float = MAX_INPUT_AMOUNT, integer: bool = False) -> None:
        if (isinstance(value, bool) or not isinstance(value, (int, float))
                or not math.isfinite(value) or not minimum <= value <= maximum
                or (integer and int(value) != value)):
            errors.append(f"{key}: expected {'whole ' if integer else ''}number "
                          f"between {minimum} and {maximum}")

    if not isinstance(as_of, date):
        raise ValueError("as_of must be a date")
    for i, person in enumerate(scenario.people):
        key = "client" if i == 0 else "spouse"
        dates_valid = isinstance(person.dob, date) and isinstance(person.plan_end, date)
        if not dates_valid:
            errors.append(f"{key}: dob and plan_end must be dates")
        elif person.dob > as_of:
            errors.append(f"{key}.dob: cannot follow as_of")
        number(f"{key}.retirement_age", person.retirement_age, 0, 120, True)
        if dates_valid and isinstance(person.retirement_age, (int, float)):
            if person.plan_end.year < as_of.year:
                errors.append(f"{key}.plan_end: must be in current year or later")
            if person.plan_end.year <= person.retirement_year:
                errors.append(f"{key}.plan_end: must follow retirement year")
            if person.plan_end.year - person.dob.year > 120:
                errors.append(f"{key}.plan_end: planning age cannot exceed 120")
        for name in ("income", "pension"):
            number(f"{key}.{name}", getattr(person, name), 0)
        number(f"{key}.cpp_percent", person.cpp_percent, 0, 100)
        number(f"{key}.oas_percent", person.oas_percent, 0, 100)
        number(f"{key}.cpp_age", person.cpp_age, 60, 70, True)
        number(f"{key}.oas_deferral", person.oas_deferral, 0, 5, True)
        if set(person.accounts) != set(ACCOUNTS):
            errors.append(f"{key}.accounts: require Cash, RRSP and TFSA exactly once")
        for name, account in person.accounts.items():
            number(f"{key}.{name}.balance", account.balance, 0)
            number(f"{key}.{name}.contribution", account.contribution, 0)
            # -100% is valid: initial contribution, then zero in later years.
            # There is no undocumented economic ceiling on indexation.
            number(f"{key}.{name}.indexation_percent", account.indexation_percent,
                   -100, math.inf)
    number("before_return_percent", scenario.before_return_percent, -100, 100)
    number("retirement_return_percent", scenario.retirement_return_percent, -100, 100)
    number("inflation_percent", scenario.inflation_percent, -99, 100)
    if (len(scenario.withdrawal_order) != 3
            or set(scenario.withdrawal_order) != set(ACCOUNTS)):
        errors.append("withdrawal_order: require Cash, RRSP and TFSA exactly once")
    if errors:
        raise ValueError("Invalid inputs:\n" + "\n".join(errors))


def scenario_from_dict(data: dict[str, Any]) -> Scenario:
    """Read the explicit JSON schema; missing fields raise a descriptive error."""
    def require_keys(record: dict, expected: set[str], label: str) -> None:
        if set(record) != expected:
            raise ValueError(f"{label}: missing {sorted(expected - set(record))}; "
                             f"unexpected {sorted(set(record) - expected)}")

    def person(record: dict[str, Any]) -> Person:
        require_keys(record, {"dob", "retirement_age", "plan_end", "income", "pension",
                              "cpp_percent", "cpp_age", "oas_percent", "oas_deferral", "accounts"}, "person")
        return Person(
            dob=date.fromisoformat(record["dob"]),
            retirement_age=record["retirement_age"],
            plan_end=date.fromisoformat(record["plan_end"]),
            income=record["income"], pension=record["pension"],
            cpp_percent=record["cpp_percent"], cpp_age=record["cpp_age"],
            oas_percent=record["oas_percent"], oas_deferral=record["oas_deferral"],
            accounts={name: Account(**account)
                      for name, account in record["accounts"].items()},
        )
    try:
        require_keys(data, {"as_of", "client", "spouse", "before_return_percent",
                            "retirement_return_percent", "inflation_percent", "withdrawal_order"}, "scenario")
        return Scenario(
            client=person(data["client"]),
            spouse=person(data["spouse"]) if data["spouse"] is not None else None,
            before_return_percent=data["before_return_percent"],
            retirement_return_percent=data["retirement_return_percent"],
            inflation_percent=data["inflation_percent"],
            withdrawal_order=tuple(data["withdrawal_order"]),
        )
    except (KeyError, TypeError, ValueError) as error:
        raise ValueError(f"Invalid scenario JSON: {error}") from error
