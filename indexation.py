"""Annual compounding and today's-dollar conversion, independent of account rules."""

import math


def annual_factor(annual_percent: float, elapsed_years: int) -> float:
    """Convert percent once: 2.5 means 0.025; t=0 always gives a factor of one."""
    if not math.isfinite(annual_percent) or annual_percent < -100:
        raise ValueError("Annual percent must be finite and at least -100")
    if not isinstance(elapsed_years, int):
        raise ValueError("Elapsed years must be an integer")
    try:
        factor = (1 + annual_percent / 100) ** elapsed_years
    except (OverflowError, ZeroDivisionError) as error:
        raise ValueError("Annual factor cannot be represented for these inputs") from error
    if not math.isfinite(factor):
        raise ValueError("Annual factor cannot be represented for these inputs")
    return factor


def indexed_amount(initial_amount: float, annual_percent: float, elapsed_years: int) -> float:
    """Nominal amount = initial amount × (1 + rate/100)^t."""
    result = initial_amount * annual_factor(annual_percent, elapsed_years)
    if not math.isfinite(result):
        raise ValueError("Indexed amount exceeds numeric capacity")
    return result


def todays_dollars(nominal: float, inflation_percent: float, elapsed_years: int) -> float:
    """Deflate by general inflation, never by an item's indexation rate."""
    if inflation_percent <= -100:
        raise ValueError("Inflation must exceed -100% for today's-dollar values")
    try:
        result = nominal / annual_factor(inflation_percent, elapsed_years)
    except ZeroDivisionError as error:
        raise ValueError("Inflation factor underflow prevents today's-dollar conversion") from error
    if not math.isfinite(result):
        raise ValueError("Today's-dollar value exceeds numeric capacity")
    return result
