import { useId, useMemo, useState, type ReactNode } from 'react';
import { ArrowDown, ArrowUpRight, Check, ChevronDown, Download, Leaf, LockKeyhole, RotateCcw, ShieldCheck, SlidersHorizontal, TrendingUp, Users, Wallet, CircleAlert } from 'lucide-react';
import { ACCOUNTS, DISCLAIMER, GOVERNMENT, currency, currentAge, defaultScenario, project, scenarioFacts, validate, type AccountType, type Person, type Scenario } from './model';
import { Chart, Table } from './Charts';

function Field({ label, value, onChange, type = 'number', prefix, suffix, error, ariaLabel, min, max, step = 'any' }: {
  label: string; value: number | string; onChange: (v: string) => void;
  type?: string; prefix?: string; suffix?: string; error?: string; ariaLabel?: string;
  min?: number; max?: number; step?: string;
}) {
  const id = useId();
  return <div className={`field ${error ? 'field-invalid' : ''}`}>
    <label htmlFor={id}>{label}</label>
    <div className={`input-wrap ${type === 'date' ? 'date-wrap' : ''}`}>
      {prefix && <span>{prefix}</span>}
      <input id={id} type={type} value={typeof value === 'number' && !Number.isFinite(value) ? '' : value}
        onChange={e => onChange(e.target.value)} aria-label={ariaLabel ?? label}
        aria-invalid={Boolean(error)} aria-describedby={error ? `${id}-error` : undefined}
        min={min} max={max} step={step} inputMode={type === 'number' ? 'decimal' : undefined} />
      {suffix && <span>{suffix}</span>}
    </div>
    {error && <span id={`${id}-error`} className="field-error">{error}</span>}
  </div>;
}

function InputCard({ number, title, subtitle, children, initiallyOpen = true }: {
  number: string; title: string; subtitle: string; children: ReactNode; initiallyOpen?: boolean;
}) {
  const [open, setOpen] = useState(initiallyOpen);
  const id = useId();
  return <section className={`input-card ${open ? 'is-open' : ''}`}>
    <button className="card-toggle" onClick={() => setOpen(!open)} aria-expanded={open} aria-controls={id}>
      <span className="step-number">{number}</span><span><strong>{title}</strong><small>{subtitle}</small></span>
      <ChevronDown size={16} className={open ? 'rotated' : ''} />
    </button>
    <div id={id} className="input-card-body" hidden={!open}>{children}</div>
  </section>;
}

const ORDERS: AccountType[][] = [
  ['Cash', 'RRSP', 'TFSA'], ['Cash', 'TFSA', 'RRSP'], ['RRSP', 'Cash', 'TFSA'],
  ['RRSP', 'TFSA', 'Cash'], ['TFSA', 'Cash', 'RRSP'], ['TFSA', 'RRSP', 'Cash'],
];

export default function App() {
  const [scenario, setScenario] = useState<Scenario>(() => defaultScenario());
  const [personKey, setPersonKey] = useState<'client' | 'spouse'>('client');
  const [tableOpen, setTableOpen] = useState(false);
  const [exporting, setExporting] = useState(false);
  const [exportError, setExportError] = useState('');
  const now = new Date();
  const errors = useMemo(() => validate(scenario), [scenario]);
  const projection = useMemo(() => Object.keys(errors).length ? null : project(scenario), [scenario, errors]);
  const person = scenario[personKey];
  const who = personKey === 'client' ? 'Client' : 'Spouse';
  const age = currentAge(person.dob);
  const setPerson = <K extends keyof Person>(key: K, value: Person[K]) => setScenario(s => ({ ...s, [personKey]: { ...s[personKey], [key]: value } }));
  const numeric = (v: string) => v.trim() === '' ? NaN : Number(v);
  const personField = (key: keyof Person, label: string, options: { type?: string; prefix?: string; suffix?: string; min?: number; max?: number; step?: string } = {}) =>
    <Field label={label} ariaLabel={`${who} ${label}`} value={person[key] as number | string} {...options}
      error={errors[`${personKey}.${key}`]} onChange={v => setPerson(key, options.type === 'date' ? v : numeric(v))} />;
  const toggleSpouse = () => {
    setScenario(s => ({ ...s, hasSpouse: !s.hasSpouse }));
    if (scenario.hasSpouse) setPersonKey('client');
  };
  const reset = () => { setScenario(defaultScenario()); setPersonKey('client'); setExportError(''); };
  const download = async () => {
    setExporting(true); setExportError('');
    try { const { exportPDF } = await import('./pdf'); await exportPDF(structuredClone(scenario)); }
    catch (error) { setExportError(error instanceof Error ? error.message : 'Unable to export. Please try again.'); }
    finally { setExporting(false); }
  };
  return <>
    <header className="site-header"><div className="header-inner">
      <a className="wordmark" href="#" aria-label="Fresh home"><span className="brand-icon"><Leaf size={22} strokeWidth={1.7} /></span>fresh<span className="wordmark-dot">.</span></a>
      <div className="header-divider" /><span className="header-name">Retirement planner</span>
      <span className="privacy-badge"><LockKeyhole size={13} /> Private by design</span>
    </div></header>
    <main className="page-shell">
      <section className="hero"><div>
        <p className="eyebrow"><span /> A clearer tomorrow starts here</p>
        <h1>Your future, <em>in perspective.</em></h1>
        <p className="hero-copy">Turn today’s savings into a picture of tomorrow.<br className="desktop-break" /> Explore your retirement, one simple scenario at a time.</p>
      </div><div className="hero-actions">
        <span className="live-note"><span /> Updates as you go</span>
        <div className="action-row"><button className="button button-subtle" onClick={reset} disabled={exporting}><RotateCcw size={15} />Reset example</button>
          <button className="button button-primary" onClick={download} disabled={!projection || exporting}><Download size={16} />{exporting ? 'Preparing PDF…' : 'Export client PDF'}</button>
        </div><span className="actions-note">A fresh copy of the scenario on your screen.</span>
      </div></section>
      {exportError && <div role="alert" className="error-banner">{exportError}</div>}
      <div className="planner-layout">
        <aside className="inputs-column" aria-label="Scenario inputs" inert={exporting}>
          <div className="column-heading"><SlidersHorizontal size={16} /><h2>Your scenario</h2><span>Make it yours</span></div>
          <InputCard number="01" title="Your household" subtitle="The people and the plan">
            <div className="spouse-toggle"><span><Users size={15} />Include spouse</span><button role="switch" aria-label="Include spouse" aria-checked={scenario.hasSpouse} className={`switch ${scenario.hasSpouse ? 'checked' : ''}`} onClick={toggleSpouse}><span /></button></div>
            {scenario.hasSpouse && <div className="person-tabs" role="tablist" aria-label="Person to edit"><button role="tab" aria-selected={personKey === 'client'} onClick={() => setPersonKey('client')}>You</button><button role="tab" aria-selected={personKey === 'spouse'} onClick={() => setPersonKey('spouse')}>Spouse</button></div>}
            <div className="field-with-age">{personField('dob', 'Date of birth', { type: 'date' })}<span className="age-note">{age !== null && age >= 0 ? `Age ${age} today` : 'Enter your birth date'}</span></div>
            <div className="two-fields">{personField('retirementAge', 'Retirement age', { min: 0, max: 120, step: '1' })}{personField('income', 'Current income', { prefix: '$', min: 0 })}</div>
            <p className="field-note">Current income is annual, before tax.</p>
            {personField('planEnd', 'Plan end date', { type: 'date' })}
            <p className="field-note">Income ends after this year. Savings remain available to a surviving spouse.</p>
            <div className="quiet-callout"><span className="tiny-icon"><TrendingUp size={14} /></span><p>Your target is <strong>100% of current income</strong>, adjusted for inflation.</p></div>
          </InputCard>
          <InputCard number="02" title="Savings & contributions" subtitle={`${who === 'Client' ? 'Your' : 'Spouse’s'} accounts, today and tomorrow`}>
            {ACCOUNTS.map(type => <div className="account-group" key={type}>
              <div className="account-title"><i className={`account-dot ${type.toLowerCase()}`} /><h3>{type}</h3><span>{type === 'Cash' ? 'Cash savings' : type === 'RRSP' ? 'Retirement savings' : 'Tax-free savings'}</span></div>
              <div className="two-fields">{(['balance', 'contribution'] as const).map(key => <Field key={key} label={key === 'balance' ? 'Current balance' : 'Annual contribution'} ariaLabel={`${who} ${type} ${key === 'balance' ? 'current balance' : 'annual contribution'}`} prefix="$" min={0} value={person.accounts[type][key]}
                error={errors[`${personKey}.${type}.${key}`]} onChange={v => setPerson('accounts', { ...person.accounts, [type]: { ...person.accounts[type], [key]: numeric(v) } })} />)}</div>
              <label className="indexing-label">Contributions<select aria-label={`${who} ${type} contribution indexing`} value={person.accounts[type].indexed ? 'indexed' : 'flat'} onChange={e => setPerson('accounts', { ...person.accounts, [type]: { ...person.accounts[type], indexed: e.target.value === 'indexed' } })}><option value="flat">Stay flat</option><option value="indexed">Grow with inflation</option></select></label>
            </div>)}
            <p className="field-note">Contributions stop in your retirement year. Income isn’t automatically invested.</p>
          </InputCard>
          <InputCard number="03" title="Pension & benefits" subtitle="Income alongside your savings" initiallyOpen={false}>
            {personField('pension', 'Annual pension payable at retirement', { prefix: '$', min: 0 })}
            <p className="field-note">Starts at your retirement. Stays fixed; no inflation indexing or survivor pension.</p>
            <div className="benefit-heading">CPP</div><div className="two-fields">{personField('cppPercent', '% of maximum CPP', { suffix: '%', min: 0, max: 100 })}{personField('cppAge', 'CPP start age', { min: 60, max: 70, step: '1' })}</div>
            <div className="benefit-heading">OAS</div><div className="two-fields">{personField('oasPercent', '% of maximum OAS', { suffix: '%', min: 0, max: 100 })}{personField('oasDeferral', 'OAS deferral years', { min: 0, max: 5, step: '1' })}</div>
            <p className="field-note">OAS starts at age {65 + (Number.isFinite(person.oasDeferral) ? person.oasDeferral : 0)}. Start-year payments are prorated by birthday.</p>
            <div className="reference-note">{GOVERNMENT.referenceYear} reference maximums<br />CPP {currency(GOVERNMENT.cppAnnualMaximum)} · OAS {currency(GOVERNMENT.oasAnnualMaximum)} / year<br />Projected forward with your inflation assumption.</div>
          </InputCard>
          <InputCard number="04" title="Shared assumptions" subtitle="A consistent lens for your plan">
            <div className="two-fields">{(['beforeReturn', 'retirementReturn'] as const).map(key => <Field key={key} label={key === 'beforeReturn' ? 'Return before retirement' : 'Return during retirement'} suffix="%" value={scenario[key]} min={-100} max={100} error={errors[key]} onChange={v => setScenario(s => ({ ...s, [key]: numeric(v) }))} />)}</div>
            <p className="field-note">Each person’s accounts switch rates at their own retirement.</p>
            <Field label="Annual inflation" suffix="%" value={scenario.inflation} min={-99} max={100} error={errors.inflation} onChange={v => setScenario(s => ({ ...s, inflation: numeric(v) }))} />
            <label className="select-field">Withdrawal order<select aria-label="Withdrawal order" value={scenario.order.join(',')} onChange={e => setScenario(s => ({ ...s, order: e.target.value.split(',') as AccountType[] }))}>{ORDERS.map(o => <option key={o.join(',')} value={o.join(',')}>{o.join(' → ')}</option>)}</select></label>
            <p className="field-note">Within each account type, withdrawals are proportional to both people’s balances.</p>
          </InputCard>
          <div className="privacy-note"><ShieldCheck size={18} /><p><strong>Your numbers stay yours.</strong> Everything runs in your browser. Nothing is stored or sent.</p></div>
        </aside>

        <section className="results-column" aria-label="Projection results">
          <div className="column-heading"><span className="result-indicator" /><h2>Your retirement picture</h2><span>Pre-tax illustration</span></div>
          {!projection ? <div className="validation-state" role="alert"><CircleAlert size={28} /><h2>A few details need a second look.</h2><p>Correct the highlighted fields to update your projection.</p><ul>{Object.entries(errors).map(([key, error]) => <li key={key}><strong>{key.replaceAll('.', ' · ')}:</strong> {error}</li>)}</ul></div> : <>
            <div className={`verdict ${projection.firstShortfall ? 'verdict-shortfall' : ''}`} data-testid="verdict" aria-live="polite">
              <div className="verdict-icon">{projection.firstShortfall ? <CircleAlert size={22} /> : <Check size={23} strokeWidth={2} />}</div>
              <div><p className="eyebrow">{projection.firstShortfall ? 'Shortfall in this scenario' : 'On track in this scenario'}</p><h2>{projection.firstShortfall ? 'A gap worth planning for.' : 'Room to look ahead.'}</h2><p>{projection.firstShortfall ? <>Your first unfunded year is <strong>{projection.firstShortfall.year}</strong>, with a gap of {currency(projection.firstShortfall.shortage)}.</> : <>Your savings and income cover all <strong>{projection.retirementYearsCount} retirement years</strong> in this illustration.</>}</p></div>
              <span className="verdict-tag">Your scenario</span>
            </div>
            <div className="metrics-grid">
              <Metric label={projection.alreadyRetired ? 'Savings at projection start' : 'Savings at first retirement'} value={currency(projection.savingsAtRetirement)} detail={projection.alreadyRetired ? 'Already retired · current savings' : `Before withdrawals · ${projection.firstRetirementYear}`} icon={<Wallet size={17} />} />
              <Metric label="Balance left at plan end" value={currency(projection.finalBalance)} detail={`After growth · ${projection.endYear}`} icon={<ArrowUpRight size={18} />} />
              <Metric label="Fully funded retirement years" value={`${projection.fundedYears}`} valueSuffix={`of ${projection.retirementYearsCount}`} detail="Years with no unfunded shortage" icon={<Check size={18} />} />
              <Metric label="First-year income target" value={currency(projection.firstTarget)} detail={`Per year · ${Math.max(now.getFullYear(), projection.firstRetirementYear)}`} icon={<TrendingUp size={17} />} />
            </div>
            <section className="results-card glance-card"><div className="section-heading"><div><span className="section-kicker">The essentials</span><h2>Scenario at a glance</h2></div><span className="subtle-chip">{scenario.hasSpouse ? 'Two-person household' : 'Your individual plan'}</span></div>
              <dl className="facts-grid">{scenarioFacts(scenario, projection).map(([label, value]) => <div key={label}><dt>{label}</dt><dd>{value}</dd></div>)}</dl>
            </section>
            <section className="results-card charts-card"><div className="section-heading"><div><span className="section-kicker">See the bigger picture</span><h2>How your plan unfolds</h2></div><span className="subtle-chip">Annual projection</span></div>
              <Chart projection={projection} kind="balance" /><div className="chart-divider" /><Chart projection={projection} kind="income" />
            </section>
            <div className="method-note"><span className="method-icon"><Leaf size={20} /></span><div><h3>A picture of possibilities, not a promise.</h3><p>These are nominal, pre-tax estimates using constant returns. A zero savings balance isn’t a shortfall if income still covers your target.</p></div></div>
          </>}
        </section>
      </div>
      {projection && <section className="results-card annual-section"><button className="annual-toggle" aria-expanded={tableOpen} aria-controls="annual-table" onClick={() => setTableOpen(!tableOpen)}><div><span className="section-kicker">Every year, accounted for</span><h2>Your year-by-year projection</h2><p>Explore the numbers behind the picture. All balances are after annual growth.</p></div><span className="table-toggle-label">{tableOpen ? 'Hide details' : 'View all years'}<ArrowDown size={17} className={tableOpen ? 'rotated' : ''} /></span></button>
        <div id="annual-table" hidden={!tableOpen}><Table projection={projection} hasSpouse={scenario.hasSpouse} /><p className="table-note"><span className="row-marker" /> Retirement year <span className="shortage-key" /> Unfunded shortage · Income-target years begin at the first retirement. Ages are blank after a person’s plan ends.</p></div>
      </section>}
      <section className="disclaimer-section"><div className="disclaimer-heading"><ShieldCheck size={17} /><h2>A few things to keep in mind</h2></div><p>{DISCLAIMER}</p><p>The current year counts as a full year. Each person retires at the start of their selected retirement year. Working income counts during partial retirement; only entered contributions add to savings. The survivor’s target uses their own original current income, adjusted for inflation.</p></section>
      <footer className="site-footer"><a href="#" className="footer-brand">fresh.</a><span>A clearer view. A more considered future.</span><span>Made for exploring, not predicting.</span></footer>
    </main>
  </>;
}

function Metric({ label, value, valueSuffix, detail, icon }: { label: string; value: string; valueSuffix?: string; detail: string; icon: ReactNode }) {
  return <div className="metric"><div className="metric-top"><span>{label}</span>{icon}</div><p className="metric-value">{value}{valueSuffix && <small>{valueSuffix}</small>}</p><span className="metric-detail">{detail}</span></div>;
}
