import { jsPDF } from 'jspdf';
import autoTable from 'jspdf-autotable';
import { ACCOUNTS, DISCLAIMER, GOVERNMENT, currency, project, retirementYear, scenarioFacts, yearOf, type Scenario } from './model';
import { BALANCE_SERIES, INCOME_SERIES } from './Charts';

async function chartImage(kind: string): Promise<string> {
  const svg = document.querySelector<SVGSVGElement>(`svg[data-chart="${kind}"]`);
  if (!svg) throw new Error('The charts are not ready yet. Please try again.');
  const copy = svg.cloneNode(true) as SVGSVGElement;
  copy.querySelectorAll('[data-hover]').forEach(element => element.remove());
  copy.setAttribute('xmlns', 'http://www.w3.org/2000/svg');
  copy.setAttribute('width', '1440'); copy.setAttribute('height', '560');
  const blob = new Blob([new XMLSerializer().serializeToString(copy)], { type: 'image/svg+xml;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  try {
    const image = new Image(); image.src = url; await image.decode();
    const canvas = document.createElement('canvas'); canvas.width = 1440; canvas.height = 560;
    const context = canvas.getContext('2d');
    if (!context) throw new Error('Your browser could not prepare the chart images.');
    context.drawImage(image, 0, 0, canvas.width, canvas.height);
    return canvas.toDataURL('image/png');
  } finally { URL.revokeObjectURL(url); }
}

export async function exportPDF(scenario: Scenario) {
  // Re-project on every click. The caller passes a new copy of the current form.
  const now = new Date();
  const p = project(scenario, now);
  const images = await Promise.all([chartImage('balance'), chartImage('income')]);
  const doc = new jsPDF({ unit: 'mm', format: 'a4' });
  const green: [number, number, number] = [21, 63, 53];
  const heading = (title: string, subtitle: string) => {
    doc.setTextColor(...green); doc.setFont('helvetica', 'bold'); doc.setFontSize(23); doc.text('fresh', 17, 22);
    doc.setFontSize(17); doc.text(title, 17, 38);
    doc.setTextColor(104, 119, 109); doc.setFont('helvetica', 'normal'); doc.setFontSize(9); doc.text(subtitle, 17, 46);
  };
  const prepared = new Intl.DateTimeFormat('en-CA', { year: 'numeric', month: 'long', day: 'numeric' }).format(now);
  heading('Your retirement, in perspective.', `Prepared ${prepared} · Canadian dollars · Pre-tax illustration`);
  doc.setFillColor(...(p.firstShortfall ? [249, 239, 226] : [232, 241, 229]) as [number, number, number]);
  doc.roundedRect(17, 54, 176, 25, 3, 3, 'F');
  doc.setFont('helvetica', 'bold'); doc.setTextColor(...green); doc.setFontSize(12);
  doc.text(p.firstShortfall ? 'SHORTFALL IN THIS SCENARIO' : 'ON TRACK IN THIS SCENARIO', 23, 64);
  doc.setFont('helvetica', 'normal'); doc.setFontSize(9);
  doc.text(p.firstShortfall ? `First unfunded year: ${p.firstShortfall.year}.` : `All ${p.retirementYearsCount} projected retirement years are fully funded.`, 23, 72);
  const metrics = [
    [p.alreadyRetired ? 'Savings at projection start (already retired)' : 'Savings at first retirement', currency(p.savingsAtRetirement)],
    ['Balance left at plan end', currency(p.finalBalance)],
    ['Fully funded retirement years', `${p.fundedYears} of ${p.retirementYearsCount}`],
    ['First-year income target', `${currency(p.firstTarget)}/year`],
  ];
  metrics.forEach(([label, value], i) => {
    const x = i % 2 ? 108 : 17, y = 92 + Math.floor(i / 2) * 24;
    doc.setTextColor(104, 119, 109); doc.setFontSize(9); doc.text(label, x, y);
    doc.setTextColor(...green); doc.setFont('helvetica', 'bold'); doc.setFontSize(17); doc.text(value, x, y + 9); doc.setFont('helvetica', 'normal');
  });
  doc.setFontSize(12); doc.setFont('helvetica', 'bold'); doc.text('Scenario at a glance', 17, 139);
  const people = [scenario.client, ...(scenario.hasSpouse ? [scenario.spouse] : [])];
  const facts = scenarioFacts(scenario, p).filter(([label]) => label !== 'Pension')
    .map(([label, value]) => [label, value.replaceAll('→', '>').replaceAll('–', '-')]);
  people.forEach((person, index) => {
    const label = index === 0 ? 'Client' : 'Spouse';
    facts.push(
      [`${label} pension`, `${currency(person.pension)}/year · fixed from ${retirementYear(person)}`],
      [`${label} CPP`, `${person.cppPercent}% of maximum · starts at age ${person.cppAge} (${yearOf(person.dob) + person.cppAge})`],
      [`${label} OAS`, `${person.oasPercent}% of maximum · ${person.oasDeferral}-year deferral · starts at ${65 + person.oasDeferral} (${yearOf(person.dob) + 65 + person.oasDeferral})`],
    );
  });
  facts.push(['Benefit references', `${GOVERNMENT.referenceYear}: CPP ${currency(GOVERNMENT.cppAnnualMaximum)} · OAS ${currency(GOVERNMENT.oasAnnualMaximum)}/year`]);
  autoTable(doc, { startY: 143, margin: { left: 17, right: 17 }, body: facts, theme: 'plain',
    styles: { fontSize: 9, cellPadding: 1.1, textColor: green, fontStyle: 'normal' },
    columnStyles: { 0: { cellWidth: 43, textColor: [104, 119, 109] } } });
  const factsEnd = (doc as jsPDF & { lastAutoTable: { finalY: number } }).lastAutoTable.finalY;
  doc.setFont('helvetica', 'normal'); doc.setTextColor(104, 119, 109); doc.setFontSize(9);
  doc.text(doc.splitTextToSize(DISCLAIMER, 176), 17, factsEnd + 8);
  doc.addPage();
  heading('The shape of your plan', 'Annual balances and retirement funding');
  const legend = (items: { label: string; color: string }[], y: number, target = false) => {
    let x = 17;
    doc.setFont('helvetica', 'normal'); doc.setFontSize(9);
    items.forEach(item => {
      doc.setFillColor(item.color); doc.roundedRect(x, y - 2.5, 3, 3, 0.5, 0.5, 'F');
      doc.setTextColor(104, 119, 109); doc.text(item.label, x + 5, y);
      x += doc.getTextWidth(item.label) + 11;
    });
    if (target) {
      doc.setDrawColor('#a86b48'); doc.setLineWidth(0.5); doc.setLineDashPattern([1.2, 0.8], 0);
      doc.line(x, y - 1, x + 5, y - 1); doc.setLineDashPattern([], 0);
      doc.text('Income target', x + 7, y);
    }
  };
  doc.setFontSize(12); doc.setFont('helvetica', 'bold'); doc.text('Your savings over time', 17, 58);
  legend(BALANCE_SERIES, 65);
  doc.addImage(images[0], 'PNG', 17, 69, 176, 68.5);
  doc.setFont('helvetica', 'normal'); doc.setFontSize(9); doc.setTextColor(104, 119, 109);
  doc.text('Balances after growth. Dashed markers show each retirement year.', 17, 144);
  doc.setTextColor(...green); doc.setFont('helvetica', 'bold'); doc.setFontSize(12); doc.text('Funding your retirement', 17, 155);
  legend(INCOME_SERIES.map(item => ({ ...item, label: item.label === 'Investments' ? 'Investment draw' : item.label })), 162, true);
  doc.setFillColor(242, 246, 237); doc.roundedRect(17, 167, 176, 12, 2, 2, 'F');
  doc.setFont('helvetica', 'normal'); doc.setFontSize(8.5); doc.setTextColor(...green);
  doc.text(doc.splitTextToSize('Working income counts in the calculation but is excluded from this chart. A visible gap alone does not mean a shortfall.', 168), 21, 172);
  doc.addImage(images[1], 'PNG', 17, 182, 176, 68.5);
  doc.setFont('helvetica', 'bold'); doc.setFontSize(10); doc.text('How to read this', 17, 259);
  doc.setFont('helvetica', 'normal'); doc.setFontSize(9); doc.setTextColor(104, 119, 109);
  doc.text(doc.splitTextToSize('All amounts are nominal, pre-tax Canadian dollars. The target rises with inflation. After one person’s plan ends, their income stops and the target uses the survivor’s original current income, adjusted for inflation.', 176), 17, 266);
  doc.addPage('a4', 'landscape');
  const heads = ['Year', 'Client\nage', ...(scenario.hasSpouse ? ['Spouse\nage'] : []), 'Target', 'Shortage', 'CPP', 'OAS', 'Pension', 'Investment\ndraw', ...ACCOUNTS, 'Total\nsavings'];
  const body = p.rows.map(r => [String(r.year) + (p.retirementYears.includes(r.year) ? '*' : ''), r.ages[0] === null ? '-' : String(r.ages[0]),
    ...(scenario.hasSpouse ? [r.ages[1] === null ? '-' : String(r.ages[1])] : []),
    r.retired ? currency(r.need) : '-', r.retired ? currency(r.shortage) : '-', currency(r.cpp), currency(r.oas), currency(r.pension), r.retired ? currency(r.draw) : '-',
    ...ACCOUNTS.map(t => currency(r.balances[t])), currency(r.total)]);
  autoTable(doc, { startY: 34, head: [heads], body, margin: { top: 34, bottom: 16, left: 12, right: 12 },
    styles: { fontSize: 8, cellPadding: 1.8, halign: 'right', textColor: green, fontStyle: 'normal' },
    headStyles: { fillColor: green, textColor: [255, 255, 255], fontSize: 8, fontStyle: 'bold' },
    alternateRowStyles: { fillColor: [245, 248, 244] },
    columnStyles: { 0: { halign: 'left', cellWidth: 16 }, 1: { cellWidth: 12 }, ...(scenario.hasSpouse ? { 2: { cellWidth: 12 } } : {}) },
    showHead: 'everyPage', rowPageBreak: 'avoid',
    willDrawPage: data => {
      doc.setFont('helvetica', 'bold'); doc.setFontSize(16); doc.setTextColor(...green);
      doc.text(`Your year-by-year projection${data.pageNumber > 1 ? ' · continued' : ''}`, 12, 18);
      doc.setFont('helvetica', 'normal'); doc.setFontSize(8.5); doc.setTextColor(104, 119, 109);
      doc.text('Household totals in CAD · Balances after growth · * Retirement year · Shaded amber: shortage', 12, 26);
    },
    didParseCell: data => {
      if (data.section !== 'body') return;
      const row = p.rows[data.row.index];
      if (p.retirementYears.includes(row.year)) {
        data.cell.styles.fillColor = [232, 241, 229];
        data.cell.styles.fontStyle = 'bold';
      }
      if (row.shortage > 0) data.cell.styles.fillColor = [249, 239, 226];
    } });
  const count = doc.getNumberOfPages();
  for (let page = 1; page <= count; page++) {
    doc.setPage(page); doc.setTextColor(104, 119, 109); doc.setFont('helvetica', 'normal'); doc.setFontSize(8);
    const height = doc.internal.pageSize.getHeight(), width = doc.internal.pageSize.getWidth();
    doc.text('Fresh · Values are estimates, not guarantees.', 17, height - 9);
    doc.text(`${page} / ${count}`, width - 17, height - 9, { align: 'right' });
  }
  doc.save('fresh-client-retirement-projection.pdf');
}
