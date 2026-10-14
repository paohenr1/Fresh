import { jsPDF } from 'jspdf';
import autoTable from 'jspdf-autotable';
import { ACCOUNTS, DISCLAIMER, GOVERNMENT, currency, currentAge, project, scenarioDate, scenarioFacts, summaryCards, type Scenario } from './model';
export type PDFKind = 'client' | 'advisor';
const green: [number,number,number] = [21,63,53];
const clean = (text: string) => text.replaceAll('→','>').replaceAll('–','-').replaceAll('—','-').replaceAll('’',"'");

/** Copy the current area chart, removing transient hover marks only. */
async function chartImage(kind: string): Promise<string> {
  const svg = document.querySelector<SVGSVGElement>(`svg[data-chart="${kind}"]`);
  if (!svg) throw new Error('The charts are not ready yet. Please try again.');
  const copy = svg.cloneNode(true) as SVGSVGElement;
  copy.querySelectorAll('[data-hover]').forEach(element => element.remove());
  copy.setAttribute('xmlns','http://www.w3.org/2000/svg');
  copy.setAttribute('width','1440'); copy.setAttribute('height','560');
  const url = URL.createObjectURL(new Blob([new XMLSerializer().serializeToString(copy)],{type:'image/svg+xml;charset=utf-8'}));
  try {
    const image = new Image(); image.src=url; await image.decode();
    const canvas=document.createElement('canvas'); canvas.width=1440; canvas.height=560;
    const context=canvas.getContext('2d');
    if (!context) throw new Error('Your browser could not prepare chart images.');
    context.drawImage(image,0,0); return canvas.toDataURL('image/png');
  } finally { URL.revokeObjectURL(url); }
}

/** One snapshot supplies every number; advisor inputs include collapsed fields.
 * Client tables are nominal; advisor tables follow the dashboard's dollar basis.
 */
export function buildPDF(s: Scenario, kind: PDFKind, real: boolean, images: string[], exportedAt=new Date()) {
  const p=project(s), doc=new jsPDF({unit:'mm',format:'a4'});
  const people=[s.client,...(s.hasSpouse ? [s.spouse] : [])];
  const tableReal=kind==='advisor' && real;
  const end=() => (doc as jsPDF & {lastAutoTable:{finalY:number}}).lastAutoTable.finalY;
  const heading=(title:string,subtitle:string) => {
    doc.setFont('helvetica','bold');doc.setTextColor(...green);doc.setFontSize(21);doc.text('fresh.',17,21);
    doc.setFont('helvetica','normal');doc.setFontSize(18);doc.text(title,17,37);
    doc.setFontSize(9);doc.setTextColor(104,119,109);doc.text(clean(subtitle),17,45);
  };
  const note=(text:string,y:number) => {
    doc.setFont('helvetica','normal');doc.setFontSize(8);doc.setTextColor(104,119,109);
    doc.text(doc.splitTextToSize(clean(text),176),17,y);
  };
  const factsTable=(rows:(string|number)[][],y:number,head:string[]) => {
    autoTable(doc,{startY:y,head:[head],body:rows.map(row=>row.map(value=>clean(String(value)))),
      margin:{top:18,bottom:17,left:17,right:17},theme:'grid',
      styles:{fontSize:8,cellPadding:2,textColor:green,lineColor:[224,231,223],lineWidth:0.1},
      headStyles:{fillColor:green,textColor:[255,255,255]},alternateRowStyles:{fillColor:[245,248,244]}});
  };
  const title=kind==='client' ? 'Client retirement report' : 'Advisor scenario record';
  heading('Your retirement, in perspective.',`${title} · Exported ${exportedAt.toISOString().slice(0,16).replace('T',' ')} UTC · CAD · Pre-tax`);
  doc.setFontSize(10);doc.setTextColor(...green);
  doc.text(p.firstShortfall ? `First unfunded year: ${p.firstShortfall.year}. Gap: ${currency(p.firstShortfall.shortage)}.` : `All ${p.retirementYearsCount} projected retirement years are fully funded.`,17,58);
  summaryCards(s,p).forEach(([label,value],i)=>{
    const x=17+i*35.2;doc.setDrawColor(212,220,229);doc.setLineWidth(0.2);doc.rect(x,68,35.2,35);
    doc.setFont('helvetica','normal');doc.setFontSize(7);doc.setTextColor(0,54,93);
    doc.text(doc.splitTextToSize(clean(label),31),x+17.6,76,{align:'center'});
    doc.setFont('helvetica','bold');doc.setFontSize(15);
    while(doc.getTextWidth(value)>31 && doc.getFontSize()>8) doc.setFontSize(doc.getFontSize()-1);
    doc.text(value,x+17.6,94,{align:'center'});
  });
  note('Current savings includes starting Cash, RRSP and TFSA balances. The annual income target is the initial retirement-year amount; later targets follow general inflation.',111);
  const facts=scenarioFacts(s,p).filter(([label])=>!['Contributions','Pension'].includes(label));
  if(kind==='client') people.forEach((person,i)=>{
    const who=i===0 ? 'Client' : 'Spouse';
    facts.push([`${who} pension`,`${currency(person.pension)}/year at retirement; ${person.pensionIndexationPercent}% annual indexation`],
      [`${who} CPP / OAS`,`CPP ${person.cppPercent}% at age ${person.cppAge}; OAS ${person.oasPercent}%, deferred ${person.oasDeferral} years`]);
  });
  factsTable(facts,122,['Scenario at a glance','Value']);note(DISCLAIMER,end()+8);
  if(kind==='advisor') people.forEach((person,i)=>{
    doc.addPage();heading('Inputs and assumptions',i===0 ? 'Shared assumptions and client inputs' : 'Spouse inputs');
    let y=53;
    if(i===0){
      factsTable([['Include spouse',s.hasSpouse ? 'Yes' : 'No'],['Return before retirement',`${s.beforeReturn}% annually`],
        ['Return during retirement',`${s.retirementReturn}% annually`],['General inflation',`${s.inflation}% annually`],
        ['Withdrawal order',s.order.join(' > ')],['Government reference year',GOVERNMENT.referenceYear],
        ['Maximum CPP / OAS reference',`CPP ${currency(GOVERNMENT.cppAnnualMaximum)}; OAS ${currency(GOVERNMENT.oasAnnualMaximum)}/year`]],y,['Shared input','Value']);y=end()+8;
    }
    const who=i===0 ? 'Client' : 'Spouse';
    // Preserve user-entered precision in the advisor's input record.
    const inputMoney=(value:number)=>new Intl.NumberFormat('en-CA',{style:'currency',currency:'CAD',minimumFractionDigits:2,maximumFractionDigits:20}).format(value);
    factsTable([['Current age',currentAge(person.dob,scenarioDate(s)) ?? '-'],['Retirement age',person.retirementAge],
      ['Age at plan end',currentAge(person.dob,new Date(`${person.planEnd}T12:00:00`)) ?? '-'],
      ['Current gross income',`${inputMoney(person.income)}/year`],['Annual pension at retirement',`${inputMoney(person.pension)}/year`],
      ['Pension indexation',`${person.pensionIndexationPercent}% annually`],['CPP percentage of maximum',`${person.cppPercent}%`],
      ['CPP start age',person.cppAge],['OAS percentage of maximum',`${person.oasPercent}%`],['OAS deferral years',person.oasDeferral]],y,[`${who} input`,'Value']);
    factsTable(ACCOUNTS.map(name=>[name,inputMoney(person.accounts[name].balance),inputMoney(person.accounts[name].contribution),`${person.accounts[name].indexationPercent}%`]),end()+8,['Account','Starting balance CAD','Annual contribution CAD','Indexation %/year']);
    if(i===people.length-1) note('2.5 means 2.5%. General inflation is separate. Contribution t=0 is the projection start year. Pension t=0 is each retirement year; already-retired people include elapsed retirement years. Collapsed inputs remain active.',end()+8);
  });
  doc.addPage();heading('The shape of your plan','Annual household values in nominal CAD');
  const legends=[[['Cash','#bbd4b1'],['RRSP','#639d83'],['TFSA','#194c3e']],[['CPP','#194c3e'],['OAS','#639d83'],['Pension','#c5ae7b'],['Investment draw','#bbd4b1']]];
  images.forEach((image,i)=>{
    const y=58+i*103;doc.setTextColor(...green);doc.setFont('helvetica','bold');doc.setFontSize(12);
    doc.text(i===0 ? 'Your savings over time' : 'Funding your retirement',17,y);
    let x=17;doc.setFont('helvetica','normal');doc.setFontSize(8);
    legends[i].forEach(([label,color])=>{doc.setFillColor(color);doc.rect(x,y+5,3,3,'F');doc.text(label,x+5,y+7.5);x+=doc.getTextWidth(label)+12;});
    if(i===1){doc.setDrawColor('#a86b48');doc.setLineDashPattern([1,1],0);doc.line(x,y+6.5,x+5,y+6.5);doc.setLineDashPattern([],0);doc.text('Target',x+7,y+7.5);}
    doc.addImage(image,'PNG',17,y+12,176,68.5);
    note(i===0 ? 'Balances after growth. Dashed markers show retirement years.' : 'Working income counts in calculations but is excluded here. A graph gap alone does not mean a shortfall.',y+86);
  });
  note('The current year is a full year. Contributions and withdrawals occur before investment growth. Contributions stop in each retirement year. After a plan ends, income stops; the survivor target follows their own original income and general inflation.',258);
  doc.addPage('a4','landscape');
  const basis=tableReal ? `Today's CAD (${p.startYear} purchasing power)` : 'Nominal CAD';
  const money=(value:number,year:number)=>currency(value/(tableReal ? Math.pow(1+s.inflation/100,year-p.startYear) : 1));
  const heads=['Year','Client\nage',...(s.hasSpouse ? ['Spouse\nage'] : []),'Target','Shortage','CPP','OAS','Pension','Investment\ndraw',...ACCOUNTS,'Total\nsavings'];
  const body=p.rows.map(r=>[String(r.year)+(p.retirementYears.includes(r.year) ? '*' : ''),r.ages[0] ?? '-',...(s.hasSpouse ? [r.ages[1] ?? '-'] : []),
    r.retired ? money(r.need,r.year) : '-',r.retired ? money(r.shortage,r.year) : '-',money(r.cpp,r.year),money(r.oas,r.year),money(r.pension,r.year),r.retired ? money(r.draw,r.year) : '-',...ACCOUNTS.map(t=>money(r.balances[t],r.year)),money(r.total,r.year)]);
  autoTable(doc,{startY:34,head:[heads],body,margin:{top:34,bottom:16,left:12,right:12},styles:{fontSize:8,cellPadding:1.8,halign:'right',textColor:green},
    headStyles:{fillColor:green,textColor:[255,255,255]},alternateRowStyles:{fillColor:[245,248,244]},showHead:'everyPage',rowPageBreak:'avoid',
    columnStyles:{0:{halign:'left',cellWidth:16},1:{cellWidth:12},...(s.hasSpouse ? {2:{cellWidth:15}} : {})},
    willDrawPage:()=>{doc.setFont('helvetica','bold');doc.setFontSize(16);doc.setTextColor(...green);doc.text('Your year-by-year projection',12,18);doc.setFont('helvetica','normal');doc.setFontSize(8.5);doc.text(`${basis} · Balances after growth · * Retirement year · Amber: shortage`,12,26);},
    didParseCell:data=>{if(data.section!=='body') return;if(p.retirementYears.includes(p.rows[data.row.index].year)) data.cell.styles.fillColor=[232,241,229];if(p.rows[data.row.index].shortage>0) data.cell.styles.fillColor=[249,239,226];}});
  const count=doc.getNumberOfPages();
  for(let page=1;page<=count;page++) {doc.setPage(page);doc.setFont('helvetica','normal');doc.setFontSize(8);doc.setTextColor(104,119,109);doc.text('Fresh · Values are estimates, not guarantees.',17,doc.internal.pageSize.getHeight()-9);doc.text(`${page} / ${count}`,doc.internal.pageSize.getWidth()-17,doc.internal.pageSize.getHeight()-9,{align:'right'});}
  return doc;
}

export async function exportPDF(scenario:Scenario,kind:PDFKind='client',real=false) {
  const images=await Promise.all([chartImage('balance'),chartImage('income')]);
  buildPDF(scenario,kind,real,images).save(`fresh-${kind}-${new Date().toISOString().slice(0,10)}.pdf`);
}
