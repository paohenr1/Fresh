import { useState } from 'react';
import { ACCOUNTS, compact, currency, type Projection, type Row } from './model';

type Series = { label: string; color: string; value: (r: Row) => number };
export const BALANCE_SERIES: Series[] = [
  { label: 'Cash', color: '#bbd4b1', value: r => r.balances.Cash },
  { label: 'RRSP', color: '#639d83', value: r => r.balances.RRSP },
  { label: 'TFSA', color: '#194c3e', value: r => r.balances.TFSA },
];
export const INCOME_SERIES: Series[] = [
  { label: 'CPP', color: '#194c3e', value: r => r.cpp },
  { label: 'OAS', color: '#639d83', value: r => r.oas },
  { label: 'Pension', color: '#c5ae7b', value: r => r.pension },
  { label: 'Investments', color: '#bbd4b1', value: r => r.draw },
];

export function Chart({ projection: p, kind, planEnds = [] }: { projection: Projection; kind: 'balance' | 'income'; planEnds?: { year: number; person: string }[] }) {
  const rows = kind === 'balance' ? p.rows : p.rows.filter(r => r.retired);
  const series = kind === 'balance' ? BALANCE_SERIES : INCOME_SERIES;
  const [hover, setHover] = useState<number | null>(null);
  const width = 720, height = 280, left = 62, right = 18, top = 26, bottom = 36;
  const innerW = width - left - right, innerH = height - top - bottom;
  const max = Math.max(1, ...rows.map(r => Math.max(series.reduce((n, s) => n + s.value(r), 0), kind === 'income' ? r.need : 0)));
  const power = Math.pow(10, Math.floor(Math.log10(max)));
  const ceiling = Math.ceil(max / (power / 2)) * (power / 2);
  const x = (i: number) => left + i / Math.max(1, rows.length - 1) * innerW;
  const y = (n: number) => top + innerH - n / ceiling * innerH;
  const paths = series.map((s, si) => {
    const upper = rows.map((r, i) => `${x(i)},${y(series.slice(0, si + 1).reduce((n, a) => n + a.value(r), 0))}`);
    const lower = rows.map((r, i) => `${x(i)},${y(series.slice(0, si).reduce((n, a) => n + a.value(r), 0))}`).reverse();
    return { ...s, points: [...upper, ...lower].join(' ') };
  });
  const tickIndices = [...new Set([0, ...[1, 2, 3].map(n => Math.round((rows.length - 1) * n / 4)), rows.length - 1])];
  const title = kind === 'balance' ? 'Your savings over time' : 'Funding your retirement';
  const selected = hover !== null ? rows[hover] : null;
  return <div className="chart-block">
    <div className="chart-heading"><h3>{title}</h3><span className="micro">CAD · nominal dollars</span></div>
    <div className="chart-legend">{series.map(s => <span key={s.label}><i style={{ background: s.color }} />{s.label}</span>)}
      {kind === 'income' && <span><i className="legend-target" />Target</span>}
    </div>
    <div className="chart-canvas" onMouseLeave={() => setHover(null)}>
      <svg data-chart={kind} viewBox={`0 0 ${width} ${height}`} role="img" aria-label={title}
        onMouseMove={e => {
          const rect = e.currentTarget.getBoundingClientRect();
          const pos = (e.clientX - rect.left) / rect.width * width;
          setHover(Math.min(rows.length - 1, Math.max(0, Math.round((pos - left) / innerW * (rows.length - 1)))));
        }}>
        <title>{title}. {kind === 'balance' ? 'Cash, RRSP and TFSA balances after annual growth.' : 'Benefits, pension and withdrawals compared with the income target. Employment income is excluded.'}</title>
        <rect width={width} height={height} fill="#ffffff" />
        {[0, 1, 2, 3, 4].map(i => <g key={i}>
          <line x1={left} x2={width - right} y1={y(ceiling * i / 4)} y2={y(ceiling * i / 4)} stroke="#e9eeea" strokeDasharray={i ? '3 4' : undefined} />
          <text x={left - 12} y={y(ceiling * i / 4) + 4} textAnchor="end" fill="#75877d" fontSize="11" fontFamily="Arial, sans-serif">{compact(ceiling * i / 4)}</text>
        </g>)}
        {paths.map(s => <polygon key={s.label} points={s.points} fill={s.color} opacity="0.96" />)}
        {kind === 'income' && <polyline points={rows.map((r, i) => `${x(i)},${y(r.need)}`).join(' ')} stroke="#a86b48" strokeWidth="2.5" strokeDasharray="6 4" fill="none" />}
        {kind === 'income' && planEnds.map(({ year, person }) => {
          const i = rows.findIndex(r => r.year === year + 1);
          return i < 0 ? null : <g key={person}>
            <line x1={x(i)} x2={x(i)} y1={top} y2={height - bottom} stroke="#7a8b7e" strokeDasharray="4 4" />
            <text x={Math.min(width - right, Math.max(left, x(i)))} y={top - 8} textAnchor={x(i) > width / 2 ? 'end' : 'start'} fill="#677c70" fontSize="12" fontFamily="Arial, sans-serif">{person} plan ends · {year}</text>
          </g>;
        })}
        {kind === 'balance' && [...new Set(p.retirementYears)].map((year, index) => {
          const i = rows.findIndex(r => r.year === year);
          return i < 0 ? null : <g key={year}>
            <line x1={x(i)} x2={x(i)} y1={top} y2={height - bottom} stroke="#7a8b7e" strokeWidth="1" strokeDasharray="4 4" />
            <text x={x(i) + 5} y={top - 8 + index * 14} fill="#677c70" fontSize="10" fontFamily="Arial, sans-serif">{p.retirementYears.length > 1 ? `${index === 0 ? 'Client' : 'Spouse'} retires` : 'Retirement'}</text>
          </g>;
        })}
        {tickIndices.map(i => <text key={i} x={x(i)} y={height - 11} textAnchor="middle" fill="#75877d" fontSize="11" fontFamily="Arial, sans-serif">{rows[i]?.year}</text>)}
        {selected && hover !== null && <line data-hover="true" x1={x(hover)} x2={x(hover)} y1={top} y2={height - bottom} stroke="#153f35" opacity="0.6" />}
      </svg>
      {selected && <div className="chart-tooltip"><strong>{selected.year}</strong>{series.map(s => <span key={s.label}>{s.label}<b>{currency(s.value(selected))}</b></span>)}{kind === 'income' && <span>Target<b>{currency(selected.need)}</b></span>}</div>}
    </div>
    <p className="chart-note">{kind === 'balance' ? 'Balances after growth. Dashed markers show retirement years.' : 'Working income counts in the projection but is excluded here. A gap in this chart alone does not mean a shortfall.'}</p>
  </div>;
}

export function Table({ projection, hasSpouse }: { projection: Projection; hasSpouse: boolean }) {
  return <div className="table-scroll" tabIndex={0} aria-label="Scrollable year-by-year projection">
    <table><thead><tr><th>Year</th><th>Client age</th>{hasSpouse && <th>Spouse age</th>}<th>Target</th><th>Shortage</th><th>CPP</th><th>OAS</th><th>Pension</th><th>Investment draw</th>{ACCOUNTS.map(t => <th key={t}>{t}</th>)}<th>Total savings</th></tr></thead>
      <tbody>{projection.rows.map(row => <tr key={row.year} className={`${projection.retirementYears.includes(row.year) ? 'retirement-row' : ''} ${row.shortage > 0 ? 'shortage-row' : ''}`}>
        <td><strong>{row.year}</strong>{projection.retirementYears.includes(row.year) && <span className="row-marker" title="Retirement year" />}</td>
        <td>{row.ages[0] ?? '—'}</td>{hasSpouse && <td>{row.ages[1] ?? '—'}</td>}
        <td>{row.retired ? currency(row.need) : '—'}</td><td className={row.shortage > 0 ? 'shortage-value' : ''}>{row.retired ? currency(row.shortage) : '—'}</td>
        <td>{currency(row.cpp)}</td><td>{currency(row.oas)}</td><td>{currency(row.pension)}</td><td>{row.retired ? currency(row.draw) : '—'}</td>
        {ACCOUNTS.map(t => <td key={t}>{currency(row.balances[t])}</td>)}<td><strong>{currency(row.total)}</strong></td>
      </tr>)}</tbody>
    </table>
  </div>;
}
