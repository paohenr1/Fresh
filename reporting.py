"""Auditable tables, source summary metrics, and a self-contained FRESH report."""

import csv
from datetime import date
from html import escape
from pathlib import Path
from typing import Any

from indexation import todays_dollars
from inputs import ACCOUNTS, GOVERNMENT, Scenario, age_on_date
from projection import Projection


def annual_table(projection: Projection, scenario: Scenario) -> list[dict[str, Any]]:
    """Return flat records with explicit nominal CAD and today's CAD suffixes."""
    records = []
    for row in projection.rows:
        record: dict[str, Any] = {
            "year": row.year, "client_age": row.ages[0],
            "spouse_age": row.ages[1] if len(row.ages) == 2 else None,
            "retired": row.retired,
        }
        amounts = {
            "opening_total": sum(row.opening_balances.values()),
            "contributions": row.contributions,
            "investment_return": sum(row.investment_returns.values()),
            "employment_income": row.employment, "cpp_income": row.cpp,
            "oas_income": row.oas, "pension_income": row.pension,
            "income_total": row.employment + row.cpp + row.oas + row.pension,
            # This target is gross income replacement, not an after-tax budget.
            "spending_target": row.need, "withdrawals": row.draw,
            "unmet_spending": row.shortage, "raw_unmet_spending": row.raw_shortage,
            "closing_total": row.total,
        }
        for name in ACCOUNTS:
            for label, values in (
                ("opening", row.opening_balances),
                ("contribution", row.contributions_by_account),
                ("withdrawal", row.withdrawals_by_account),
                ("return", row.investment_returns), ("closing", row.balances),
            ):
                amounts[f"{name.lower()}_{label}"] = values[name]
        for label, nominal in amounts.items():
            record[f"{label}_nominal_cad"] = nominal
            record[f"{label}_today_cad"] = todays_dollars(
                nominal, scenario.inflation_percent, row.year - projection.start_year)
        records.append(record)
    return records


def summary(projection: Projection, scenario: Scenario) -> dict[str, Any]:
    """Preserve original metrics; supplement monetary metrics with real values."""
    first = max(projection.start_year, projection.first_retirement_year)
    result: dict[str, Any] = {
        "verdict": "ON TRACK IN THIS SCENARIO" if projection.first_shortfall is None
                   else "SHORTFALL IN THIS SCENARIO",
        "start_year": projection.start_year, "end_year": projection.end_year,
        "retirement_years": list(projection.retirement_years),
        "first_retirement_year": projection.first_retirement_year,
        "already_retired": projection.already_retired,
        "fully_funded_retirement_years": projection.funded_years,
        "retirement_years_count": projection.retirement_years_count,
        "first_shortfall_year": projection.first_shortfall.year if projection.first_shortfall else None,
        "today_dollar_base_year": projection.start_year,
    }
    for label, amount, year in (
        ("starting_savings", projection.starting_savings, projection.start_year),
        ("savings_at_first_retirement", projection.savings_at_retirement, first),
        ("first_year_income_target", projection.first_target, first),
        ("balance_left_at_plan_end", projection.final_balance, projection.end_year),
    ):
        result[f"{label}_nominal_cad"] = amount
        result[f"{label}_today_cad"] = todays_dollars(
            amount, scenario.inflation_percent, year - projection.start_year)
    return result


def write_csv(records: list[dict[str, Any]], path: Path) -> None:
    """Write full-precision audit values; display rounding belongs in reports."""
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(records[0]))
        writer.writeheader()
        writer.writerows(records)


def _money(value: float) -> str:
    """Match the original whole-dollar display; exports keep full precision."""
    from decimal import Decimal, ROUND_HALF_UP

    rounded = Decimal(str(value)).quantize(Decimal('1'), rounding=ROUND_HALF_UP)
    return f"${rounded:,.0f}"


def _icon(name: str, size: int = 17) -> str:
    """Inline line icons keep the report self-contained, including offline."""
    paths = {
        "leaf": '<path d="M11 20A7 7 0 0 1 9.8 6.1C15.5 5 17 4.5 19 2c1 2 2 4.2 2 8 0 5.5-4.8 10-10 10Z"/><path d="M2 22c0-6 6-12 12-14"/>',
        "check": '<path d="m20 6-11 11-5-5"/>',
        "arrow": '<path d="M7 17 17 7M7 7h10v10"/>',
        "trend": '<path d="m3 17 6-6 4 4 8-10M15 5h6v6"/>',
        "wallet": '<path d="M20 8V5a2 2 0 0 0-2-2H6a3 3 0 0 0 0 6h14v11H6a3 3 0 0 1-3-3V6M20 12h-4v4h4"/>',
        "chevron": '<path d="m6 9 6 6 6-6"/>',
        "download": '<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4M7 10l5 5 5-5M12 15V3"/>',
        "shield": '<path d="M12 22s8-4 8-11V5l-8-3-8 3v6c0 7 8 11 8 11Z"/><path d="m9 12 2 2 4-4"/>',
        "lock": '<rect x="3" y="11" width="18" height="11" rx="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4M12 15v3"/>',
        "sliders": '<path d="M4 21v-7M4 10V3M12 21v-9M12 8V3M20 21v-5M20 12V3M1 14h6M9 8h6M17 16h6"/>',
        "alert": '<circle cx="12" cy="12" r="10"/><path d="M12 8v4M12 16h.01"/>',
        "users": '<path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2M22 21v-2a4 4 0 0 0-3-3.9M16 3.1a4 4 0 0 1 0 7.8"/><circle cx="9" cy="7" r="4"/>',
    }
    return (f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" '
            f'stroke="currentColor" stroke-width="1.7" stroke-linecap="round" '
            f'stroke-linejoin="round" aria-hidden="true">{paths[name]}</svg>')


def _chart(projection: Projection, scenario: Scenario, kind: str) -> str:
    """Port Charts.tsx: stacked area polygons, the same scale, ticks and markers."""
    import json
    import math

    rows = projection.rows if kind == "balance" else [r for r in projection.rows if r.retired]
    if not rows:
        return '<p class="chart-note">The projection ends before retirement begins.</p>'
    series = ([("Cash", "#bbd4b1", lambda r: r.balances["Cash"]),
               ("RRSP", "#639d83", lambda r: r.balances["RRSP"]),
               ("TFSA", "#194c3e", lambda r: r.balances["TFSA"])] if kind == "balance" else
              [("CPP", "#194c3e", lambda r: r.cpp), ("OAS", "#639d83", lambda r: r.oas),
               ("Pension", "#c5ae7b", lambda r: r.pension),
               ("Investments", "#bbd4b1", lambda r: r.draw)])
    title = "Your savings over time" if kind == "balance" else "Funding your retirement"
    # SVG coordinates match the original 720 × 280 chart exactly.
    width, height, left, right, top, bottom = 720, 280, 62, 18, 26, 36
    inner_width, inner_height = width - left - right, height - top - bottom
    maximum = max(1, *(max(sum(fn(r) for _, _, fn in series), r.need if kind == "income" else 0) for r in rows))
    power = 10 ** math.floor(math.log10(maximum))
    ceiling = math.ceil(maximum / (power / 2)) * (power / 2)

    def x(index: int) -> float:
        return left + index / max(1, len(rows) - 1) * inner_width

    def y(value: float) -> float:
        return top + inner_height - value / ceiling * inner_height

    def compact(value: float) -> str:
        if abs(value) >= 1_000_000:
            return f"${value / 1_000_000:.1f}m"
        return f"${math.floor(value / 1000 + .5)}k" if abs(value) >= 1000 else _money(value)

    shapes = [f'<title>{title}</title><rect width="720" height="280" fill="#fff"/>']
    for tick in range(5):
        amount = ceiling * tick / 4
        dash = ' stroke-dasharray="3 4"' if tick else ''
        shapes.append(f'<line x1="{left}" x2="{width-right}" y1="{y(amount)}" y2="{y(amount)}" stroke="#e9eeea"{dash}/>'
                      f'<text x="{left-12}" y="{y(amount)+4}" text-anchor="end" fill="#75877d" font-size="11" font-family="Arial,sans-serif">{compact(amount)}</text>')
    for index, (label, color, _) in enumerate(series):
        # Upper and lower cumulative boundaries create each continuous filled band.
        upper = [f'{x(i)},{y(sum(fn(r) for _, _, fn in series[:index+1]))}' for i, r in enumerate(rows)]
        lower = [f'{x(i)},{y(sum(fn(r) for _, _, fn in series[:index]))}' for i, r in enumerate(rows)][::-1]
        shapes.append(f'<polygon data-series="{label}" points="{" ".join(upper+lower)}" fill="{color}" opacity="0.96"/>')
    if kind == "income":
        points = " ".join(f"{x(i)},{y(r.need)}" for i, r in enumerate(rows))
        shapes.append(f'<polyline points="{points}" stroke="#a86b48" stroke-width="2.5" stroke-dasharray="6 4" fill="none"/>')
        markers = [(p.plan_end.year + 1, f'{"Client" if i == 0 else "Spouse"} plan ends · {p.plan_end.year}') for i, p in enumerate(scenario.people)]
    else:
        markers = [(year, ("Client retires" if i == 0 else "Spouse retires") if len(projection.retirement_years) > 1 else "Retirement")
                   for i, year in enumerate(dict.fromkeys(projection.retirement_years))]
    for index, (year, label) in enumerate(markers):
        position = next((i for i, r in enumerate(rows) if r.year == year), None)
        if position is None:
            continue
        xx = x(position)
        anchor = "end" if kind == "income" and xx > width / 2 else "start"
        text_x = xx + 5 if kind == "balance" else xx
        text_y = top - 8 + (index * 14 if kind == "balance" else 0)
        shapes.append(f'<line x1="{xx}" x2="{xx}" y1="{top}" y2="{height-bottom}" stroke="#7a8b7e" stroke-dasharray="4 4"/>'
                      f'<text x="{text_x}" y="{text_y}" text-anchor="{anchor}" fill="#677c70" font-size="{10 if kind == "balance" else 12}" font-family="Arial,sans-serif">{escape(label)}</text>')
    ticks = sorted({0, *(math.floor((len(rows)-1)*n/4 + .5) for n in (1, 2, 3)), len(rows)-1})
    for index in ticks:
        shapes.append(f'<text x="{x(index)}" y="269" text-anchor="middle" fill="#75877d" font-size="11" font-family="Arial,sans-serif">{rows[index].year}</text>')
    shapes.append('<line class="hover-line" x1="62" x2="62" y1="26" y2="244" stroke="#153f35" opacity="0.6" visibility="hidden"/>')
    hover_rows = [{"year": r.year, "values": [[label, _money(fn(r))] for label, _, fn in series] +
                   ([["Target", _money(r.need)]] if kind == "income" else [])} for r in rows]
    legend = ''.join(f'<span><i style="background:{color}"></i>{label}</span>' for label, color, _ in series)
    if kind == "income":
        legend += '<span><i class="legend-target"></i>Target</span>'
    note = ("Balances after growth. Dashed markers show retirement years." if kind == "balance" else
            "Working income counts in the projection but is excluded here. A gap in this chart alone does not mean a shortfall.")
    return (f'<div class="chart-block"><div class="chart-heading"><h3>{title}</h3><span class="micro">CAD · nominal dollars</span></div>'
            f'<div class="chart-legend">{legend}</div><div class="chart-canvas" data-rows="{escape(json.dumps(hover_rows), quote=True)}">'
            f'<svg data-chart="{kind}" viewBox="0 0 720 280" role="img" aria-label="{title}" tabindex="0">{"".join(shapes)}</svg>'
            f'<div class="chart-tooltip" hidden></div></div><p class="chart-note">{note}</p></div>')


def _sidebar(scenario: Scenario, as_of: date, interactive: bool = False) -> str:
    """Render scenario fields; editable mode sends values to the Python engine."""
    key, account_name = "client", None
    def field(label: str, value: object, prefix: str = "", suffix: str = "") -> str:
        names = {"Birth date": "dob", "Retirement age": "retirement_age", "Current income": "income",
                 "End date": "plan_end", "Annual pension payable at retirement": "pension",
                 "% of maximum CPP": "cpp_percent", "CPP start age": "cpp_age",
                 "% of maximum OAS": "oas_percent", "OAS deferral years": "oas_deferral",
                 "Current balance": "balance", "Annual contribution": "contribution",
                 "Annual contribution increase": "indexation_percent",
                 "Annual pension increase": "pension_indexation_percent",
                 "Return before retirement": "before_return_percent", "Return during retirement": "retirement_return_percent",
                 "Annual inflation": "inflation_percent", "Withdrawal order": "withdrawal_order"}
        name = names[label]
        shared = name in ("before_return_percent", "retirement_return_percent", "inflation_percent", "withdrawal_order", "as_of")
        path = name if shared else f'{key}.accounts.{account_name}.{name}' if name in ("balance", "contribution", "indexation_percent") else f'{key}.{name}'
        kind = "date" if name in ("dob", "plan_end", "as_of") else "number"
        attrs = f'data-input="{path}" type="{kind}" step="any" required' if interactive else 'readonly'
        if name == "withdrawal_order" and interactive:
            from itertools import permutations
            options = ''.join(f'<option value="{",".join(order)}" {"selected" if " → ".join(order) == value else ""}>{" → ".join(order)}</option>' for order in permutations(ACCOUNTS))
            return f'<label class="select-field">{label}<select data-input="withdrawal_order">{options}</select></label>'
        return (f'<div class="field"><label>{escape(label)}<span class="input-wrap">'
                f'<span>{prefix}</span><input {attrs} value="{escape(str(value), quote=True)}" aria-label="{escape(label, quote=True)}">'
                f'<span>{suffix}</span></span></label></div>')

    def pair(first: str, second: str) -> str:
        return f'<div class="two-fields">{first}{second}</div>'

    def indexation_editor(label: str, rate: float) -> str:
        """Collapse only presentation; the rate remains part of the scenario."""
        suffix = f' · {rate}%/year' if rate != 0 else ''
        if not interactive:
            return field(label, rate, suffix="%")
        return (f'<details class="date-edit indexation-edit"><summary>Edit indexation{suffix}</summary>'
                f'{field(label, rate, suffix="%")}</details>')

    def age_field(label: str, birthday: date, on: date, name: str, date_label: str, value: date) -> str:
        age = age_on_date(birthday, on)
        editor = (f'<details class="date-edit"><summary>Edit date</summary>{field(date_label, value)}</details>' if interactive else '')
        return (f'<div class="field"><label>{label}<span class="input-wrap"><input readonly aria-readonly="true" '
                f'data-age="{key}.{name}" value="{age}" aria-label="{label}" title="Calculated from the exact date; use Edit date."></span></label>{editor}</div>')

    def card(number: str, title: str, subtitle: str, body: str, opened: bool = True) -> str:
        return (f'<section class="input-card {"is-open" if opened else ""}"><button class="card-toggle" '
                f'aria-expanded="{str(opened).lower()}" aria-controls="card-{number}"><span class="step-number">{number}</span>'
                f'<span><strong>{title}</strong><small>{subtitle}</small></span>{_icon("chevron",16)}</button>'
                f'<div id="card-{number}" class="input-card-body" {"" if opened else "hidden"}>{body}</div></section>')

    household, accounts, benefits = [], [], []
    people = scenario.people if scenario.spouse or not interactive else (scenario.client, scenario.client)
    for i, person in enumerate(people):
        key = "client" if i == 0 else "spouse"
        def panel(body: str) -> str:
            return f'<div data-person="{key}" {"hidden" if i else ""}>{body}</div>'
        household.append(panel(age_field("Current age", person.dob, as_of, 'current_age', 'Birth date', person.dob) +
            pair(field("Retirement age", person.retirement_age), field("Current income", f"{person.income:g}", "$")) +
            '<p class="field-note">Current income is annual, before tax.</p>' + age_field("Age at plan end", person.dob, person.plan_end, 'plan_end_age', 'End date', person.plan_end) +
            '<p class="field-note">Income ends after this year. Savings remain available to a surviving spouse.</p>' +
            f'<div class="quiet-callout"><span class="tiny-icon">{_icon("trend",14)}</span><p>Your target is <strong>100% of current income</strong>, adjusted for inflation.</p></div>'))
        account_blocks = []
        for name in ACCOUNTS:
            account_name = name
            account = person.accounts[name]
            description = {"Cash": "Cash savings", "RRSP": "Retirement savings", "TFSA": "Tax-free savings"}[name]
            account_blocks.append(f'<div class="account-group"><div class="account-title"><i class="account-dot {name.lower()}"></i><h3>{name}</h3><span>{description}</span></div>' +
                pair(field("Current balance", f"{account.balance:g}", "$"),
                     '<div>' + field("Annual contribution", f"{account.contribution:g}", "$") +
                     indexation_editor("Annual contribution increase", account.indexation_percent) + '</div>') + '</div>')
        account_blocks.append('<p class="field-note">0% keeps contributions flat; 2.5% increases them by 2.5% each year. Separate from inflation and investment returns.</p>')
        accounts.append(panel(''.join(account_blocks) + '<p class="field-note">Contributions stop in your retirement year. Income isn’t automatically invested.</p>'))
        benefits.append(panel(field("Annual pension payable at retirement", f"{person.pension:g}", "$") +
            indexation_editor("Annual pension increase", person.pension_indexation_percent) +
            '<p class="field-note pension-note">The entered pension is the retirement-year amount. Annual increases start the following year. No survivor pension is modeled.</p><div class="benefit-heading">CPP</div>' +
            pair(field("% of maximum CPP", person.cpp_percent, suffix="%"), field("CPP start age", person.cpp_age)) +
            '<div class="benefit-heading">OAS</div>' +
            pair(field("% of maximum OAS", person.oas_percent, suffix="%"), field("OAS deferral years", person.oas_deferral)) +
            f'<p class="field-note">OAS starts at age {65+person.oas_deferral}. Start-year payments are prorated by birthday.</p>' +
            f'<div class="reference-note">{GOVERNMENT.reference_year} reference maximums<br>CPP {_money(GOVERNMENT.cpp_annual_maximum)} · OAS {_money(GOVERNMENT.oas_annual_maximum)} / year<br>Projected forward with your inflation assumption.</div>'))
    spouse = (f'<div class="spouse-toggle"><span>{_icon("users",15)}Include spouse</span><span class="switch {"checked" if scenario.spouse else ""}" aria-label="Spouse {"included" if scenario.spouse else "not included"}"><span></span></span></div>')
    if interactive:
        spouse = f'<div class="spouse-toggle"><span>{_icon("users",15)}Include spouse</span><button id="include-spouse" role="switch" aria-label="Include spouse" aria-checked="{str(scenario.spouse is not None).lower()}" class="switch {"checked" if scenario.spouse else ""}"><span></span></button></div>'
    tabs = ('<div class="person-tabs" aria-label="Person to view"><button data-person-tab="client" aria-pressed="true" aria-selected="true">You</button><button data-person-tab="spouse" aria-pressed="false" aria-selected="false">Spouse</button></div>' if scenario.spouse else '')
    if interactive and not tabs:
        tabs = '<div class="person-tabs" hidden><button data-person-tab="client" aria-selected="true">You</button><button data-person-tab="spouse" aria-selected="false">Spouse</button></div>'
    shared = (pair(field("Return before retirement", scenario.before_return_percent, suffix="%"),
                   field("Return during retirement", scenario.retirement_return_percent, suffix="%")) +
              '<p class="field-note">Each person’s accounts switch rates at their own retirement.</p>')
    shared += field("Annual inflation", scenario.inflation_percent, suffix="%") + field("Withdrawal order", ' → '.join(scenario.withdrawal_order))
    shared += '<p class="field-note">Within each account type, withdrawals are proportional to both people’s balances.</p>'
    return (card("01", "Your household", "The people and the plan", spouse + tabs + ''.join(household)) +
            card("02", "Savings &amp; contributions", "Accounts, today and tomorrow", ''.join(accounts)) +
            card("03", "Pension &amp; benefits", "Income alongside your savings", ''.join(benefits), False) +
            card("04", "Shared assumptions", "A consistent lens for your plan", shared) +
            f'<div class="privacy-note">{_icon("shield",18)}<p><strong>Your numbers stay yours.</strong>{"Calculations run in Python on this computer. Export an advisor PDF to keep a record of your inputs and results." if interactive else "Saved report. For editable inputs, run python app.py from the project folder and open the address it prints."}</p></div>')


def _annual_html(projection: Projection, scenario: Scenario, basis: str) -> str:
    """Match the original annual table, highlighting retirement transition years."""
    fields = [("spending_target", "Target"), ("unmet_spending", "Shortage"), ("cpp_income", "CPP"),
              ("oas_income", "OAS"), ("pension_income", "Pension"), ("withdrawals", "Investment draw"),
              ("cash_closing", "Cash"), ("rrsp_closing", "RRSP"), ("tfsa_closing", "TFSA"), ("closing_total", "Total savings")]
    titles = ["Year", "Client age"] + (["Spouse age"] if scenario.spouse else []) + [label for _, label in fields]
    header = ''.join(f'<th scope="col">{label}</th>' for label in titles)
    body = []
    for record in annual_table(projection, scenario):
        retirement = record['year'] in projection.retirement_years
        shortage = record[f'unmet_spending_{basis}'] > 0
        marker = '<span class="row-marker" title="Retirement year"></span>' if retirement else ''
        cells = f'<td><strong>{record["year"]}</strong>{marker}</td>'
        for age in (["client_age", "spouse_age"] if scenario.spouse else ["client_age"]):
            cells += f'<td>{record[age] if record[age] is not None else "—"}</td>'
        for field, _ in fields:
            amount = _money(record[f'{field}_{basis}'])
            if not record['retired'] and field in ("spending_target", "unmet_spending", "withdrawals"):
                amount = "—"
            if field == "closing_total":
                amount = f'<strong>{amount}</strong>'
            cells += f'<td class="{"shortage-value" if field == "unmet_spending" and shortage else ""}">{amount}</td>'
        body.append(f'<tr class="{"retirement-row" if retirement else ""} {"shortage-row" if shortage else ""}">{cells}</tr>')
    return f'<div class="table-scroll" tabindex="0" aria-label="{basis} year-by-year projection"><table><thead><tr>{header}</tr></thead><tbody>{"".join(body)}</tbody></table></div>'


def summary_card_data(projection: Projection, scenario: Scenario) -> list[tuple[str, str, str]]:
    """Share card labels and displayed values between the dashboard and both PDFs."""
    first = max(projection.start_year, projection.first_retirement_year)
    retirement_label = "Savings at projection start" if projection.already_retired else "Savings at retirement"
    retirement_label += f" · {first}" if scenario.spouse or projection.already_retired else f" · age {scenario.client.retirement_age}"
    end_label = f"Balance at plan end · {projection.end_year}" if scenario.spouse else f"Balance at plan end · age {age_on_date(scenario.client.dob, scenario.client.plan_end)}"
    return [
        (f"Current savings · {projection.start_year}", _money(projection.starting_savings), "Cash + RRSP + TFSA · household total"),
        (retirement_label, _money(projection.savings_at_retirement),
         "Already retired · current savings" if projection.already_retired else f"Before withdrawals · {projection.first_retirement_year}"),
        (end_label, _money(projection.final_balance), f"After growth · {projection.end_year}"),
        ("Years covered", f'{projection.funded_years} of {projection.retirement_years_count}', "Years with no unfunded shortage"),
        ("Annual income target", _money(projection.first_target) + "/yr", f"Initial retirement-year target · {first}"),
    ]


def render_html(projection: Projection, scenario: Scenario, live_inputs: dict | None = None) -> str:
    """Embed the original FRESH styles with Python-generated values and area graphs."""
    from string import Template

    metrics = summary_card_data(projection, scenario)
    metrics_html = ''.join(f'<article class="metric" title="{escape(detail, quote=True)}"><div class="metric-top"><span>{escape(label)}</span></div><p class="metric-value">{escape(value)}</p></article>' for label, value, detail in metrics)
    facts = [
        ("Timeline", f'{projection.start_year}–{projection.end_year} · {"First retirement" if scenario.spouse else "Retirement"} {projection.first_retirement_year}'),
        ("Starting savings", _money(projection.starting_savings)),
        ("Current income", f'{_money(sum(p.income for p in scenario.people))}/year · 100% target'),
        ("Returns", f'{scenario.before_return_percent:g}% before · {scenario.retirement_return_percent:g}% during retirement'),
        ("Inflation", f'{scenario.inflation_percent:g}% annually'),
        ("Contributions", f'{_money(sum(a.contribution for p in scenario.people for a in p.accounts.values()))}/year initially'),
        ("Withdrawal order", ' → '.join(scenario.withdrawal_order)),
        *[("Client plan" if i == 0 else "Spouse plan", f'Current age {age_on_date(p.dob, projection.as_of)} · retirement age {p.retirement_age} · age at plan end {age_on_date(p.dob, p.plan_end)}') for i, p in enumerate(scenario.people)],
        ("Pension", "Fixed annual payment from each person’s retirement"),
    ]
    gap = projection.first_shortfall
    detail = (f'Your first unfunded year is <strong>{gap.year}</strong>, with a gap of {_money(gap.shortage)}.' if gap else
              f'Your savings and income cover all <strong>{projection.retirement_years_count} retirement years</strong> in this illustration.')
    root = Path(__file__).parent
    template = Template((root / "report_template.html").read_text(encoding="utf-8"))
    html = template.substitute(
        css=(root / "report.css").read_text(encoding="utf-8"),
        leaf=_icon("leaf",22), lock=_icon("lock",13), download=_icon("download",16), sliders=_icon("sliders",16),
        shield=_icon("shield",18), chevron=_icon("chevron",17),
        sidebar=_sidebar(scenario, projection.as_of, live_inputs is not None), verdict_class="verdict-shortfall" if gap else "",
        verdict_icon=_icon("alert" if gap else "check",23),
        verdict_label="Shortfall in this scenario" if gap else "On track in this scenario",
        verdict_heading="A gap worth planning for." if gap else "Room to look ahead.", verdict_detail=detail,
        metrics=metrics_html, household="Two-person household" if scenario.spouse else "Your individual plan",
        facts=''.join(f'<div><dt>{escape(k)}</dt><dd>{escape(v)}</dd></div>' for k, v in facts),
        balance_chart=_chart(projection, scenario, "balance"), income_chart=_chart(projection, scenario, "income"),
        nominal_table=_annual_html(projection, scenario, "nominal_cad"), real_table=_annual_html(projection, scenario, "today_cad"),
        base_year=projection.start_year,
        live_script=_live_script(live_inputs),
    )
    return html


def _live_script(data: dict | None) -> str:
    """Embed initial inputs safely; no financial formulas run in JavaScript."""
    import json
    if data is None:
        return ''
    encoded = json.dumps(data, allow_nan=False).replace('<', '\\u003c')
    script = (Path(__file__).parent / 'planner.js').read_text(encoding='utf-8')
    return f'<script type="application/json" id="initial-inputs">{encoded}</script><script>{script}</script>'


def write_html(projection: Projection, scenario: Scenario, path: Path) -> None:
    """Save a standalone snapshot; app.py serves the editable version."""
    path.write_text(render_html(projection, scenario), encoding="utf-8")
