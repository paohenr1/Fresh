import { jsPDF } from 'jspdf';
import autoTable from 'jspdf-autotable';
import { ACCOUNTS, DISCLAIMER, currency, project, scenarioFacts, type Scenario } from './model';

async function chartImage(kind: string): Promise<string> {
  const svg = document.querySelector<SVGSVGElement>(`svg[data-chart="${kind}"]`);
  if (!svg) throw new Error('The charts are not ready yet. Please try again.');
  const copy = svg.cloneNode(true) as SVGSVGElement;
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
    doc.setTextColor(104, 119, 109); doc.setFontSize(8); doc.text(label, x, y);
    doc.setTextColor(...green); doc.setFont('helvetica', 'bold'); doc.setFontSize(17); doc.text(value, x, y + 9); doc.setFont('helvetica', 'normal');
  });
  doc.setFontSize(12); doc.setFont('helvetica', 'bold'); doc.text('Scenario at a glance', 17, 147);
  const facts = scenarioFacts(scenario, p).map(([label, value]) => [label, value.replaceAll('→', '>').replaceAll('–', '-')]);
  autoTable(doc, { startY: 151, margin: { left: 17, right: 17 }, body: facts, theme: 'plain',
    styles: { fontSize: 8, cellPadding: 1.4, textColor: green }, columnStyles: { 0: { cellWidth: 43, textColor: [104, 119, 109] } } });
  doc.setTextColor(104, 119, 109); doc.setFontSize(7);
  doc.text(doc.splitTextToSize(DISCLAIMER, 176), 17, 226);
  doc.addPage();
  heading('The shape of your plan', 'Annual balances and retirement funding');
  doc.setFontSize(12); doc.setFont('helvetica', 'bold'); doc.text('Your savings over time', 17, 59);
  doc.addImage(images[0], 'PNG', 17, 65, 176, 68.5);
  doc.setFont('helvetica', 'normal'); doc.setFontSize(8); doc.text('Cash / RRSP / TFSA · Balances after growth · Dashed retirement markers', 17, 139);
  doc.setFont('helvetica', 'bold'); doc.setFontSize(12); doc.text('Funding your retirement', 17, 155);
  doc.addImage(images[1], 'PNG', 17, 161, 176, 68.5);
  doc.setFont('helvetica', 'normal'); doc.setFontSize(8); doc.text('CPP / OAS / Pension / Investment withdrawals · Dashed income target', 17, 235);
  doc.setFont('helvetica', 'bold'); doc.setFontSize(10); doc.text('How to read this', 17, 249);
  doc.setFont('helvetica', 'normal'); doc.setFontSize(8);
  doc.text(doc.splitTextToSize('The first chart shows savings after each year’s growth. The second shows benefits, pension and investment withdrawals against the target. Working income counts in the calculation but is excluded from this chart, so a visible gap alone is not a shortfall. All amounts are nominal, pre-tax Canadian dollars.', 176), 17, 256);
  doc.addPage('a4', 'landscape');
  doc.setFont('helvetica', 'bold'); doc.setFontSize(17); doc.setTextColor(...green); doc.text('Your year-by-year projection', 12, 19);
  doc.setFont('helvetica', 'normal'); doc.setFontSize(8); doc.text('Household totals in CAD · Balances after annual growth · A dash means not applicable', 12, 26);
  const heads = ['Year', 'Client\nage', ...(scenario.hasSpouse ? ['Spouse\nage'] : []), 'Target', 'Shortage', 'CPP', 'OAS', 'Pension', 'Investment\ndraw', ...ACCOUNTS, 'Total\nsavings'];
  const body = p.rows.map(r => [String(r.year), r.ages[0] === null ? '-' : String(r.ages[0]),
    ...(scenario.hasSpouse ? [r.ages[1] === null ? '-' : String(r.ages[1])] : []),
    r.retired ? currency(r.need) : '-', r.retired ? currency(r.shortage) : '-', currency(r.cpp), currency(r.oas), currency(r.pension), r.retired ? currency(r.draw) : '-',
    ...ACCOUNTS.map(t => currency(r.balances[t])), currency(r.total)]);
  autoTable(doc, { startY: 32, head: [heads], body, margin: { top: 15, bottom: 16, left: 12, right: 12 },
    styles: { fontSize: 7, cellPadding: 2.1, halign: 'right', textColor: green },
    headStyles: { fillColor: green, fontSize: 7 }, alternateRowStyles: { fillColor: [245, 248, 244] },
    columnStyles: { 0: { halign: 'left' } }, showHead: 'everyPage',
    didParseCell: data => { if (data.section === 'body' && p.rows[data.row.index]?.shortage > 0) data.cell.styles.fillColor = [249, 239, 226]; } });
  const count = doc.getNumberOfPages();
  for (let page = 1; page <= count; page++) {
    doc.setPage(page); doc.setTextColor(104, 119, 109); doc.setFont('helvetica', 'normal'); doc.setFontSize(7);
    const height = doc.internal.pageSize.getHeight(), width = doc.internal.pageSize.getWidth();
    doc.text('Fresh · Values are estimates, not guarantees.', 17, height - 9);
    doc.text(`${page} / ${count}`, width - 17, height - 9, { align: 'right' });
  }
  doc.save('fresh-client-retirement-projection.pdf');
}
