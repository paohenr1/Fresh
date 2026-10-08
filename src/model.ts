export const ACCOUNTS = ['Cash', 'RRSP', 'TFSA'] as const;
export type AccountType = typeof ACCOUNTS[number];
export type Account = { balance: number; contribution: number; indexed: boolean };
export type Person = {
  dob: string; retirementAge: number; planEnd: string; income: number;
  pension: number; cppPercent: number; cppAge: number; oasPercent: number;
  oasDeferral: number; accounts: Record<AccountType, Account>;
};
export type Scenario = {
  client: Person; spouse: Person; hasSpouse: boolean;
  beforeReturn: number; retirementReturn: number; inflation: number;
  order: AccountType[];
};

// Update these together when using newly published government reference amounts.
// These are the figures specified for this illustration, not a live rate feed.
export const GOVERNMENT = { referenceYear: 2026, cppAnnualMaximum: 18092, oasAnnualMaximum: 8908 };

export const DISCLAIMER = 'Values are estimates, not guarantees. This is a gross, pre-tax illustration. Income taxes, OAS clawback, GIS, RRIF minimums, LIF maximums, pension splitting, fees, survivor pensions and CPP survivor benefits are excluded. RRSP and TFSA balances do not represent equal spendable income after tax. Retirement and plan endpoints use annual approximations. Pensions stay fixed; government reference amounts are extrapolated with inflation. Remaining savings are assumed available to a surviving spouse without modelling legal transfers or estate taxes.';

export type Row = {
  year: number; ages: (number | null)[]; retired: boolean;
  need: number; employment: number; cpp: number; oas: number; pension: number;
  draw: number; shortage: number; contributions: number;
  balances: Record<AccountType, number>; total: number;
};
export type Projection = {
  rows: Row[]; startYear: number; endYear: number;
  retirementYears: number[]; firstRetirementYear: number;
  savingsAtRetirement: number; startingSavings: number; finalBalance: number;
  firstTarget: number; fundedYears: number; retirementYearsCount: number;
  firstShortfall: Row | undefined; alreadyRetired: boolean;
};
export type ValidationErrors = Record<string, string>;

export const currency = (value: number) => new Intl.NumberFormat('en-CA', {
  style: 'currency', currency: 'CAD', maximumFractionDigits: 0,
}).format(value);
export const compact = (value: number) => {
  if (Math.abs(value) >= 1e6) return `$${(value / 1e6).toFixed(1)}m`;
  if (Math.abs(value) >= 1e3) return `$${Math.round(value / 1e3)}k`;
  return currency(value);
};
export const yearOf = (date: string) => Number(date.slice(0, 4));
export const retirementYear = (person: Person) => yearOf(person.dob) + person.retirementAge;
export function currentAge(dob: string, now = new Date()) {
  const [year, month, day] = dob.split('-').map(Number);
  if (!year || !month || !day) return null;
  return now.getFullYear() - year - (now.getMonth() + 1 < month ||
    (now.getMonth() + 1 === month && now.getDate() < day) ? 1 : 0);
}
export function defaultScenario(now = new Date()): Scenario {
  const y = now.getFullYear();
  const person = (age: number, income: number): Person => ({
    dob: `${y - age}-06-15`, retirementAge: 65, planEnd: `${y + 95 - age}-12-31`,
    income, pension: 18000, cppPercent: 100, cppAge: 65, oasPercent: 100,
    oasDeferral: 0,
    accounts: {
      Cash: { balance: 25000, contribution: 2000, indexed: false },
      RRSP: { balance: 220000, contribution: 12000, indexed: false },
      TFSA: { balance: 90000, contribution: 6000, indexed: false },
    },
  });
  return { client: person(45, 65000), spouse: person(42, 55000), hasSpouse: false,
    beforeReturn: 6, retirementReturn: 4, inflation: 2, order: [...ACCOUNTS] };
}
const validDate = (date: string) => {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(date)) return false;
  const d = new Date(`${date}T00:00:00Z`);
  return !Number.isNaN(d.getTime()) && d.toISOString().slice(0, 10) === date;
};
export function validate(s: Scenario, now = new Date()): ValidationErrors {
  const errors: ValidationErrors = {};
  const today = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')}`;
  const check = (key: string, n: number, min: number, max = Number.MAX_SAFE_INTEGER) => {
    if (!Number.isFinite(n) || n < min || n > max) errors[key] = `Enter a number from ${min.toLocaleString()} to ${max.toLocaleString()}.`;
  };
  ([['client', s.client], ...(s.hasSpouse ? [['spouse', s.spouse]] : [])] as [string, Person][]).forEach(([key, p]) => {
    if (!validDate(p.dob) || p.dob > today) errors[`${key}.dob`] = 'Enter a valid date of birth, no later than today.';
    if (!validDate(p.planEnd)) errors[`${key}.planEnd`] = 'Enter a valid plan end date.';
    check(`${key}.retirementAge`, p.retirementAge, 0, 120);
    if (!Number.isInteger(p.retirementAge)) errors[`${key}.retirementAge`] = 'Use a whole age.';
    if (validDate(p.planEnd) && validDate(p.dob)) {
      if (yearOf(p.planEnd) < now.getFullYear()) errors[`${key}.planEnd`] = 'Plan end must be in the current year or later.';
      if (yearOf(p.planEnd) <= retirementYear(p)) errors[`${key}.planEnd`] = 'Plan end must be after the retirement year.';
      if (yearOf(p.planEnd) - yearOf(p.dob) > 120) errors[`${key}.planEnd`] = 'Choose a planning age of 120 or younger.';
      if (retirementYear(p) < yearOf(p.dob)) errors[`${key}.retirementAge`] = 'Retirement must follow birth.';
    }
    for (const name of ['income', 'pension'] as const) check(`${key}.${name}`, p[name], 0);
    check(`${key}.cppPercent`, p.cppPercent, 0, 100);
    check(`${key}.oasPercent`, p.oasPercent, 0, 100);
    check(`${key}.cppAge`, p.cppAge, 60, 70);
    check(`${key}.oasDeferral`, p.oasDeferral, 0, 5);
    if (!Number.isInteger(p.cppAge)) errors[`${key}.cppAge`] = 'Use a whole age from 60 to 70.';
    if (!Number.isInteger(p.oasDeferral)) errors[`${key}.oasDeferral`] = 'Use whole years from 0 to 5.';
    for (const type of ACCOUNTS) {
      check(`${key}.${type}.balance`, p.accounts[type].balance, 0);
      check(`${key}.${type}.contribution`, p.accounts[type].contribution, 0);
    }
  });
  check('beforeReturn', s.beforeReturn, -100, 100);
  check('retirementReturn', s.retirementReturn, -100, 100);
  check('inflation', s.inflation, -99, 100);
  if (s.order.length !== 3 || new Set(s.order).size !== 3 || s.order.some(x => !ACCOUNTS.includes(x))) errors.order = 'Use Cash, RRSP and TFSA exactly once.';
  return errors;
}

/** Birthday payment starts on the birthday, inclusive. UTC avoids DST errors. */
export function birthdayFraction(dob: string, age: number, year: number) {
  const [birthYear, month, day] = dob.split('-').map(Number);
  if (year < birthYear + age) return 0;
  if (year > birthYear + age) return 1;
  // A February 29 birthday uses February 28 in non-leap start years.
  const leap = new Date(Date.UTC(year, 1, 29)).getUTCMonth() === 1;
  const birthday = Date.UTC(year, month - 1, month === 2 && day === 29 && !leap ? 28 : day);
  return (Date.UTC(year + 1, 0, 1) - birthday) /
    (Date.UTC(year + 1, 0, 1) - Date.UTC(year, 0, 1));
}
export function benefit(p: Person, type: 'cpp' | 'oas', year: number, inflation: number) {
  if (year > yearOf(p.planEnd)) return 0;
  const cpp = type === 'cpp';
  const age = cpp ? p.cppAge : 65 + p.oasDeferral;
  const adjustment = cpp ? Math.min(1.42, Math.max(0.64,
    1 + (age - 65) * 12 * (age < 65 ? 0.006 : 0.007))) : 1 + p.oasDeferral * 12 * 0.006;
  const maximum = cpp ? GOVERNMENT.cppAnnualMaximum : GOVERNMENT.oasAnnualMaximum;
  return maximum * (cpp ? p.cppPercent : p.oasPercent) / 100 * adjustment *
    Math.pow(1 + inflation / 100, year - GOVERNMENT.referenceYear) * birthdayFraction(p.dob, age, year);
}

export function project(s: Scenario, now = new Date()): Projection {
  const errors = validate(s, now);
  if (Object.keys(errors).length) throw new Error('Correct the input errors before projecting.');
  const people = [s.client, ...(s.hasSpouse ? [s.spouse] : [])];
  const startYear = now.getFullYear();
  const retirementYears = people.map(retirementYear);
  const firstRetirementYear = Math.min(...retirementYears);
  const endYear = Math.max(...people.map(p => yearOf(p.planEnd)));
  const balances = people.map(p => Object.fromEntries(ACCOUNTS.map(t => [t, p.accounts[t].balance])) as Record<AccountType, number>);
  const sumBalances = () => Object.fromEntries(ACCOUNTS.map(t => [t, balances.reduce((sum, b) => sum + b[t], 0)])) as Record<AccountType, number>;
  const startingSavings = Object.values(sumBalances()).reduce((a, b) => a + b, 0);
  let savingsAtRetirement = startingSavings;
  let firstTarget = 0;
  const rows: Row[] = [];
  for (let year = startYear; year <= endYear; year++) {
    const active = people.map(p => year <= yearOf(p.planEnd));
    // Transfer before the year after a plan ends, retaining account categories.
    if (people.length === 2) for (let i = 0; i < 2; i++) {
      if (!active[i] && active[1 - i]) for (const type of ACCOUNTS) {
        balances[1 - i][type] += balances[i][type];
        balances[i][type] = 0;
      }
    }
    const retired = year >= firstRetirementYear;
    if (year === Math.max(startYear, firstRetirementYear)) savingsAtRetirement = Object.values(sumBalances()).reduce((a, b) => a + b, 0);
    const inflationFactor = Math.pow(1 + s.inflation / 100, year - startYear);
    let contributions = 0;
    people.forEach((p, i) => {
      if (active[i] && year < retirementYears[i]) for (const type of ACCOUNTS) {
        const amount = p.accounts[type].contribution * (p.accounts[type].indexed ? inflationFactor : 1);
        balances[i][type] += amount;
        contributions += amount;
      }
    });
    const need = retired ? people.reduce((sum, p, i) => sum + (active[i] ? p.income * inflationFactor : 0), 0) : 0;
    const employment = people.reduce((sum, p, i) => sum + (active[i] && year < retirementYears[i] ? p.income * inflationFactor : 0), 0);
    const pension = people.reduce((sum, p, i) => sum + (active[i] && year >= retirementYears[i] ? p.pension : 0), 0);
    const cpp = people.reduce((sum, p) => sum + benefit(p, 'cpp', year, s.inflation), 0);
    const oas = people.reduce((sum, p) => sum + benefit(p, 'oas', year, s.inflation), 0);
    let remaining = retired ? Math.max(0, need - employment - pension - cpp - oas) : 0;
    let draw = 0;
    for (const type of s.order) {
      const total = balances.reduce((sum, b) => sum + b[type], 0);
      const withdrawal = Math.min(remaining, total);
      if (total > 0) balances.forEach(b => { b[type] = Math.max(0, b[type] - withdrawal * b[type] / total); });
      remaining = Math.max(0, remaining - withdrawal);
      draw += withdrawal;
    }
    people.forEach((_, i) => {
      const rate = year < retirementYears[i] ? s.beforeReturn : s.retirementReturn;
      for (const type of ACCOUNTS) balances[i][type] *= 1 + rate / 100;
    });
    const totals = sumBalances();
    const row: Row = { year, ages: people.map((p, i) => active[i] ? year - yearOf(p.dob) : null),
      retired, need, employment, pension, cpp, oas, contributions, draw,
      shortage: remaining < 0.000001 ? 0 : remaining, balances: totals,
      total: Object.values(totals).reduce((a, b) => a + b, 0) };
    if (year === Math.max(startYear, firstRetirementYear)) firstTarget = need;
    rows.push(row);
  }
  const retirementRows = rows.filter(r => r.retired);
  return { rows, startYear, endYear, retirementYears, firstRetirementYear,
    startingSavings, savingsAtRetirement, firstTarget, finalBalance: rows.at(-1)!.total,
    fundedYears: retirementRows.filter(r => r.shortage === 0).length,
    retirementYearsCount: retirementRows.length, firstShortfall: retirementRows.find(r => r.shortage > 0),
    alreadyRetired: firstRetirementYear < startYear };
}

export function scenarioFacts(s: Scenario, p: Projection) {
  const people = [s.client, ...(s.hasSpouse ? [s.spouse] : [])];
  return [
    ['Timeline', `${p.startYear}–${p.endYear} · ${s.hasSpouse ? 'First retirement' : 'Retirement'} ${p.firstRetirementYear}`],
    ['Starting savings', currency(p.startingSavings)],
    ['Current income', `${currency(people.reduce((n, x) => n + x.income, 0))}/year · 100% target`],
    ['Returns', `${s.beforeReturn}% before · ${s.retirementReturn}% during retirement`],
    ['Inflation', `${s.inflation}% annually`],
    ['Contributions', `${currency(people.reduce((n, x) => n + ACCOUNTS.reduce((a, t) => a + x.accounts[t].contribution, 0), 0))}/year initially`],
    ['Withdrawal order', s.order.join(' → ')],
    ...people.map((x, i) => [i === 0 ? 'Client plan' : 'Spouse plan', `Retire ${retirementYear(x)} · plan ends ${x.planEnd}`]),
    ['Pension', 'Fixed annual payment from each person’s retirement'],
  ];
}
