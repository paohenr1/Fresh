"""Client presentation and advisor scenario PDFs, using the Python projection engine."""

from datetime import date, datetime, timezone
from io import BytesIO
import math
from xml.sax.saxutils import escape

from reportlab.graphics.shapes import Drawing, Line, Polygon, PolyLine, Rect, String
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.pdfgen.canvas import Canvas
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.platypus import (BaseDocTemplate, Frame, KeepTogether, NextPageTemplate,
                               PageBreak, PageTemplate, Paragraph, Spacer, Table, TableStyle)

from inputs import ACCOUNTS, GOVERNMENT, Scenario, scenario_from_dict, age_on_date
from projection import Projection, project
from reporting import _money, annual_table, summary_card_data

GREEN = colors.HexColor('#153f35')
MUTED = colors.HexColor('#78877b')
LINE = colors.HexColor('#e3e9df')
SOFT = colors.HexColor('#f5f7f2')
STYLES = getSampleStyleSheet()
for name, size, leading, color in [('TitleFresh', 24, 29, GREEN), ('SectionFresh', 15, 20, GREEN),
                                  ('BodyFresh', 9, 13, GREEN), ('NoteFresh', 8, 11, MUTED),
                                  ('ValueFresh', 18, 23, GREEN), ('LabelFresh', 8, 11, MUTED)]:
    STYLES.add(ParagraphStyle(name=name, fontName='Helvetica', fontSize=size, leading=leading,
                              textColor=color, spaceAfter=6))


def _paragraph(text: object, style: str = 'BodyFresh') -> Paragraph:
    """Escape input text before placing it in ReportLab's small markup language."""
    return Paragraph(escape(str(text)), STYLES[style])


class _NumberedCanvas(Canvas):
    """Add page totals after the document has been laid out."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_pages = []

    def showPage(self):
        self._saved_pages.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        total = len(self._saved_pages)
        for state in self._saved_pages:
            self.__dict__.update(state)
            width, _ = self._pagesize
            self.setFillColor(MUTED)
            self.setFont('Helvetica', 8)
            self.drawString(42, 23, 'fresh.  |  Values are estimates, not guarantees.')
            self.drawRightString(width - 42, 23, f'{self._pageNumber} / {total}')
            super().showPage()
        super().save()


def _header(canvas: Canvas, doc: BaseDocTemplate) -> None:
    width, height = canvas._pagesize
    canvas.saveState()
    canvas.setFillColor(GREEN)
    canvas.setFont('Helvetica-Bold', 13)
    canvas.drawString(42, height - 30, 'fresh.')
    canvas.setFont('Helvetica', 8)
    canvas.setFillColor(MUTED)
    canvas.drawRightString(width - 42, height - 30, doc.title)
    canvas.setStrokeColor(LINE)
    canvas.line(42, height - 39, width - 42, height - 39)
    canvas.restoreState()


def _table(title: str, headers: list[str], rows: list[list], width: float,
           projection: Projection | None = None, numeric: bool = True) -> Table:
    """Repeat the caption and column headings on every continuation page."""
    size = 7.4 if len(headers) > 9 else 8.2
    header_style = ParagraphStyle('TableHeading', fontName='Helvetica-Bold', fontSize=size,
                                  leading=size + 2, textColor=colors.white)
    body_style = ParagraphStyle('TableBody', fontName='Helvetica', fontSize=size,
                                leading=size + 2, textColor=GREEN,
                                alignment=TA_RIGHT if numeric else TA_LEFT)
    caption = _paragraph(title, 'BodyFresh')
    converted = [[caption] + [''] * (len(headers) - 1),
                 [Paragraph(escape(label).replace('\n', '<br/>'), header_style) for label in headers]]
    converted += [[Paragraph(escape(str(value)), body_style) for value in row] for row in rows]
    widths = [width / len(headers)] * len(headers)
    if numeric and len(headers) > 5:
        widths[0] = 40
        widths[1:] = [(width - 40) / (len(headers) - 1)] * (len(headers) - 1)
    table = Table(converted, colWidths=widths, repeatRows=2, hAlign='LEFT')
    commands = [('SPAN', (0, 0), (-1, 0)), ('BACKGROUND', (0, 0), (-1, 0), SOFT),
                ('BACKGROUND', (0, 1), (-1, 1), GREEN), ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('TOPPADDING', (0, 0), (-1, -1), 5), ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
                ('LEFTPADDING', (0, 0), (-1, -1), 5), ('RIGHTPADDING', (0, 0), (-1, -1), 5),
                ('LINEBELOW', (0, 1), (-1, -1), .3, LINE)]
    for index in range(len(rows)):
        background = SOFT if index % 2 else colors.white
        if projection is not None:
            row = projection.rows[index]
            if row.year in projection.retirement_years:
                background = colors.HexColor('#e8f1e5')
            if row.shortage > 0:
                background = colors.HexColor('#f9efe2')
        commands.append(('BACKGROUND', (0, index + 2), (-1, index + 2), background))
    table.setStyle(TableStyle(commands))
    return table


def _summary_cards(p: Projection, scenario: Scenario, width: float) -> Table:
    """Match the approved five-box strip, with equal headings and aligned values."""
    ink = colors.HexColor('#00365d')
    border = colors.HexColor('#d4dce5')
    cell_width = width / 5
    label_style = ParagraphStyle('CardLabel', fontName='Helvetica', fontSize=8,
                                 leading=10, textColor=ink, alignment=TA_CENTER)
    cells = []
    for label, value, _ in summary_card_data(p, scenario):
        # Reserve two label lines so every value sits at the same vertical position.
        heading = Table([[Paragraph(escape(label.replace(' · ', ' - ')), label_style)]],
                        colWidths=[cell_width - 12], rowHeights=[22])
        heading.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'TOP'),
                                    ('LEFTPADDING', (0, 0), (-1, -1), 0), ('RIGHTPADDING', (0, 0), (-1, -1), 0),
                                    ('TOPPADDING', (0, 0), (-1, -1), 0), ('BOTTOMPADDING', (0, 0), (-1, -1), 0)]))
        size = min(17, (cell_width - 12) / stringWidth(value, 'Helvetica-Bold', 1))
        value_style = ParagraphStyle('CardValue', fontName='Helvetica-Bold', fontSize=size,
                                     leading=21, alignment=TA_CENTER, textColor=ink)
        cells.append([heading, Spacer(1, 5), Paragraph(escape(value), value_style)])
    table = Table([cells], colWidths=[cell_width] * 5, rowHeights=[74], hAlign='LEFT')
    table.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'TOP'),
                              ('BOX', (0, 0), (-1, -1), .5, border), ('INNERGRID', (0, 0), (-1, -1), .5, border),
                              ('BACKGROUND', (0, 0), (-1, -1), colors.white),
                              ('LEFTPADDING', (0, 0), (-1, -1), 6), ('RIGHTPADDING', (0, 0), (-1, -1), 6),
                              ('TOPPADDING', (0, 0), (-1, -1), 13), ('BOTTOMPADDING', (0, 0), (-1, -1), 10)]))
    return table


def _chart(p: Projection, scenario: Scenario, kind: str, width: float) -> Drawing:
    """Draw the same stacked annual area bands as the dashboard, as PDF vectors."""
    rows = p.rows if kind == 'balance' else [row for row in p.rows if row.retired]
    height, left, right, top, bottom = 225, 50, 12, 47, 29
    drawing = Drawing(width, height)
    if not rows:
        drawing.add(String(0, 170, 'Projection ends before retirement begins.', fontSize=9, fillColor=MUTED))
        return drawing
    series = ([(name, color, lambda row, name=name: row.balances[name]) for name, color in
               zip(ACCOUNTS, ('#bbd4b1', '#639d83', '#194c3e'))] if kind == 'balance' else
              [('CPP', '#194c3e', lambda r: r.cpp), ('OAS', '#639d83', lambda r: r.oas),
               ('Pension', '#c5ae7b', lambda r: r.pension), ('Investments', '#bbd4b1', lambda r: r.draw)])
    maximum = max(1, *(max(sum(fn(r) for _, _, fn in series), r.need if kind == 'income' else 0) for r in rows))
    power = 10 ** math.floor(math.log10(maximum))
    ceiling = math.ceil(maximum / (power / 2)) * power / 2
    inner_w, inner_h = width - left - right, height - top - bottom
    x = lambda i: left + i / max(1, len(rows) - 1) * inner_w
    y = lambda value: bottom + value / ceiling * inner_h
    legend_x = left
    for label, color, _ in series:
        drawing.add(Rect(legend_x, height - 11, 6, 6, fillColor=colors.HexColor(color), strokeColor=None))
        drawing.add(String(legend_x + 10, height - 11, label, fontSize=8, fillColor=MUTED))
        legend_x += 74
    if kind == 'income':
        drawing.add(Line(legend_x, height - 8, legend_x + 12, height - 8,
                         strokeColor=colors.HexColor('#a86b48'), strokeDashArray=[3, 2]))
        drawing.add(String(legend_x + 16, height - 11, 'Target', fontSize=8, fillColor=MUTED))
    for tick in range(5):
        amount = ceiling * tick / 4
        label = f'${amount/1e6:.1f}m' if abs(amount) >= 1e6 else f'${math.floor(amount/1000+.5)}k' if abs(amount) >= 1000 else _money(amount)
        drawing.add(Line(left, y(amount), width-right, y(amount), strokeColor=LINE, strokeDashArray=[3, 4]))
        drawing.add(String(left - 8, y(amount) - 3, label, textAnchor='end', fontSize=8, fillColor=MUTED))
    for index, (_, color, _) in enumerate(series):
        upper = [(x(i), y(sum(fn(r) for _, _, fn in series[:index+1]))) for i, r in enumerate(rows)]
        lower = [(x(i), y(sum(fn(r) for _, _, fn in series[:index]))) for i, r in enumerate(rows)][::-1]
        drawing.add(Polygon([coordinate for point in upper+lower for coordinate in point],
                            fillColor=colors.HexColor(color), strokeColor=None))
    if kind == 'income':
        drawing.add(PolyLine([v for i, row in enumerate(rows) for v in (x(i), y(row.need))],
                            strokeColor=colors.HexColor('#a86b48'), strokeWidth=1.6, strokeDashArray=[6, 4]))
        markers = [(person.plan_end.year + 1, f'{"Client" if i == 0 else "Spouse"} plan ends {person.plan_end.year}') for i, person in enumerate(scenario.people)]
    else:
        markers = [(year, ('Client retires' if i == 0 else 'Spouse retires') if len(p.retirement_years) > 1 else 'Retirement') for i, year in enumerate(dict.fromkeys(p.retirement_years))]
    for marker_index, (year, label) in enumerate(markers):
        index = next((i for i, row in enumerate(rows) if row.year == year), None)
        if index is not None:
            drawing.add(Line(x(index), bottom, x(index), height-top, strokeColor=MUTED, strokeDashArray=[4, 4]))
            anchor = 'end' if x(index) > width / 2 else 'start'
            drawing.add(String(x(index), height-top+8+marker_index*10, label, textAnchor=anchor, fontSize=7, fillColor=MUTED))
    ticks = sorted({0, *(math.floor((len(rows)-1)*n/4+.5) for n in (1, 2, 3)), len(rows)-1})
    for index in ticks:
        drawing.add(String(x(index), 10, str(rows[index].year), textAnchor='middle', fontSize=8, fillColor=MUTED))
    return drawing


def _input_sections(s: Scenario, data: dict, width: float) -> list:
    """Print both people's settings, expressing their dates as ages for the advisor."""
    as_of = date.fromisoformat(data['as_of'])
    shared = [('Include spouse', 'Yes' if s.spouse else 'No'),
              ('Return before retirement', f'{s.before_return_percent}% annually'),
              ('Return during retirement', f'{s.retirement_return_percent}% annually'),
              ('General inflation', f'{s.inflation_percent}% annually'),
              ('Withdrawal order', ' > '.join(s.withdrawal_order)),
              ('Government reference year', GOVERNMENT.reference_year),
              ('Maximum CPP reference', f'CAD {GOVERNMENT.cpp_annual_maximum:,}/year'),
              ('Maximum OAS reference', f'CAD {GOVERNMENT.oas_annual_maximum:,}/year')]
    parts = [_paragraph('Inputs and assumptions', 'SectionFresh'),
             _table('Shared assumptions and fixed source references', ['Input', 'Value'], shared, width, numeric=False), Spacer(1, 14)]
    for index, person in enumerate(s.people):
        label = 'Client' if index == 0 else 'Spouse'
        fields = [('Current age', age_on_date(person.dob, as_of)), ('Retirement age', person.retirement_age),
                  ('Age at plan end', age_on_date(person.dob, person.plan_end)), ('Current gross income', f'CAD {person.income:,}/year'),
                  ('Annual pension at retirement', f'CAD {person.pension:,}/year'),
                  ('Pension indexation', f'{person.pension_indexation_percent}% annually'),
                  ('CPP percentage of maximum', f'{person.cpp_percent}%'), ('CPP start age', person.cpp_age),
                  ('OAS percentage of maximum', f'{person.oas_percent}%'), ('OAS deferral years', person.oas_deferral)]
        accounts = [[name, f'${a.balance:,}', f'${a.contribution:,}', f'{a.indexation_percent}%']
                    for name in ACCOUNTS for a in [person.accounts[name]]]
        parts += [KeepTogether([_paragraph(label, 'SectionFresh'),
                               _table(label + ' personal inputs', ['Input', 'Value'], fields, width, numeric=False)]),
                  Spacer(1, 8), _table(label + ' accounts', ['Account', 'Starting balance\nCAD', 'Annual contribution\nCAD', 'Contribution\nincrease %/year'], accounts, width), Spacer(1, 16)]
    parts.append(_paragraph('Percentage inputs use percentage numbers: 2.5 means 2.5%. Contribution and pension rates are independent of general inflation. Contributions use the projection start year as t = 0. Pensions use each person\'s retirement year as t = 0; increases start the following year, including elapsed retirement years for already-retired people. Collapsed dashboard fields remain active and are listed here.', 'NoteFresh'))
    parts.append(_paragraph('Current age is measured at scenario start; age at plan end uses the selected end date. The annual projection table shows ages reached during each calendar year.', 'NoteFresh'))
    return parts


def export_pdf(data: dict, kind: str = 'client', exported_at: datetime | None = None,
               basis: str = 'nominal_cad') -> bytes:
    """Validate current inputs and generate a complete in-memory PDF snapshot."""
    if kind not in ('client', 'advisor'):
        raise ValueError('PDF kind must be client or advisor')
    if basis not in ('nominal_cad', 'today_cad'):
        raise ValueError('PDF table basis must be nominal_cad or today_cad')
    if kind == 'client':
        basis = 'nominal_cad'
    scenario = scenario_from_dict(data)
    p = project(scenario, date.fromisoformat(data['as_of']))
    timestamp = exported_at or datetime.now(timezone.utc)
    if timestamp.tzinfo is None:
        raise ValueError('exported_at must include a time zone')
    prepared = timestamp.astimezone(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')
    stream = BytesIO()
    title = 'Client retirement report' if kind == 'client' else 'Advisor scenario record'
    doc = BaseDocTemplate(stream, pagesize=A4, title='FRESH - ' + title, author='FRESH',
                          leftMargin=42, rightMargin=42, topMargin=54, bottomMargin=42)
    portrait_w = A4[0] - 84
    landscape_w = landscape(A4)[0] - 84
    templates = []
    for name, size in [('portrait', A4), ('landscape', landscape(A4))]:
        templates.append(PageTemplate(name, [Frame(42, 42, size[0]-84, size[1]-96,
                                                  leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)],
                                      onPage=_header, pagesize=size))
    doc.addPageTemplates(templates)
    verdict = (f'First unfunded year: {p.first_shortfall.year}. Gap: {_money(p.first_shortfall.shortage)}.' if p.first_shortfall else
               f'All {p.retirement_years_count} projected retirement years are fully funded.')
    story = [_paragraph('Your retirement, in perspective.', 'TitleFresh'), _paragraph(title, 'SectionFresh'),
             _paragraph(f'Exported {prepared} | CAD | Gross, pre-tax estimates', 'NoteFresh'),
             _paragraph('SHORTFALL IN THIS SCENARIO' if p.first_shortfall else 'ON TRACK IN THIS SCENARIO', 'BodyFresh'),
             _paragraph(verdict), Spacer(1, 8), _summary_cards(p, scenario, portrait_w), Spacer(1, 8),
             _paragraph('Current savings includes starting Cash, RRSP and TFSA balances. The annual income target is the initial retirement-year amount; subsequent targets follow general inflation.', 'NoteFresh'), Spacer(1, 12)]
    facts = [('Timeline', f'{p.start_year}-{p.end_year}'), ('General inflation', f'{scenario.inflation_percent}% annually'),
             ('Investment returns', f'{scenario.before_return_percent}% before / {scenario.retirement_return_percent}% during retirement'),
             ('Withdrawal order', ' > '.join(scenario.withdrawal_order))]
    if kind == 'client':
        for index, person in enumerate(scenario.people):
            who = 'Client' if index == 0 else 'Spouse'
            facts += [(who + ' current age', age_on_date(person.dob, p.as_of)),
                      (who + ' plan', f'Retirement age {person.retirement_age}; age at plan end {age_on_date(person.dob, person.plan_end)}'),
                      (who + ' pension', f'{_money(person.pension)}/year at retirement; {person.pension_indexation_percent}% annual indexation'),
                      (who + ' CPP / OAS', f'CPP {person.cpp_percent}% at age {person.cpp_age}; OAS {person.oas_percent}% deferred {person.oas_deferral} years')]
    story += [_table('Scenario at a glance', ['Assumption', 'Value'], facts, portrait_w, numeric=False), Spacer(1, 12),
              _paragraph('Displayed dashboard amounts are nominal CAD rounded to whole dollars. Values are estimates, not guarantees. This deterministic model excludes income taxes, OAS clawback, GIS, RRIF/LIF limits, fees, pension splitting and survivor benefits.', 'NoteFresh')]
    if kind == 'advisor':
        story += [PageBreak(), *_input_sections(scenario, data, portrait_w)]
    story += [PageBreak(), _paragraph('The shape of your plan', 'TitleFresh'),
              _paragraph('Annual household values in nominal CAD', 'NoteFresh')]
    for chart_kind, heading, note in [('balance', 'Your savings over time', 'Balances after growth. Dashed markers show retirement years.'),
                                     ('income', 'Funding your retirement', 'Employment income is included in calculations but excluded from this graph. A graph gap alone does not mean a shortfall.')]:
        story += [KeepTogether([_paragraph(heading, 'SectionFresh'), _chart(p, scenario, chart_kind, portrait_w), _paragraph(note, 'NoteFresh')]), Spacer(1, 14)]
    story += [_paragraph('The current year is a full year. Retirement begins at the start of the selected year. Withdrawals occur before annual investment growth; contributions stop in each person\'s retirement year. Once either person retires, income above the household target is added to Cash before annual growth. Allocation follows each person\'s positive income excess over their own target share; their Cash earns their applicable return rate. Before either person retires, only entered contributions add savings. After a plan ends, that person\'s income stops and the survivor\'s target uses their own original income, adjusted for inflation.', 'NoteFresh'),
              NextPageTemplate('landscape'), PageBreak()]
    records = annual_table(p, scenario)
    # Use exactly the dashboard columns and its whole-dollar formatting.
    label = 'Nominal CAD' if basis == 'nominal_cad' else f"Today's CAD ({p.start_year} purchasing power)"
    headings = ['Year', 'Client\nage'] + (['Spouse\nage'] if scenario.spouse else [])
    fields = [('spending_target', 'Target'), ('unmet_spending', 'Shortage'), ('cpp_income', 'CPP'), ('oas_income', 'OAS'),
              ('pension_income', 'Pension'), ('withdrawals', 'Investment\ndraw'), ('cash_closing', 'Cash'),
              ('rrsp_closing', 'RRSP'), ('tfsa_closing', 'TFSA'), ('closing_total', 'Total\nsavings')]
    body = []
    for r in records:
        row = [str(r['year']) + ('*' if r['year'] in p.retirement_years else ''), r['client_age'] if r['client_age'] is not None else '-']
        if scenario.spouse:
            row.append(r['spouse_age'] if r['spouse_age'] is not None else '-')
        row += ['-' if not r['retired'] and key in ('spending_target', 'unmet_spending', 'withdrawals') else _money(r[key+'_'+basis]) for key, _ in fields]
        body.append(row)
    story += [_paragraph('Your year-by-year projection', 'SectionFresh'),
              _paragraph(label + ' - household totals after growth - * retirement year - amber indicates shortage', 'NoteFresh'),
              _table(('Client' if kind == 'client' else 'Advisor') + ' annual projection - ' + label,
                     headings + [name for _, name in fields], body, landscape_w, p)]
    doc.build(story, canvasmaker=_NumberedCanvas)
    return stream.getvalue()
