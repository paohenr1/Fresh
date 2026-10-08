import { describe, expect, it } from 'vitest';
import { ACCOUNTS, GOVERNMENT, benefit, birthdayFraction, currentAge, defaultScenario, project, validate, type Person, type Scenario } from './model';

const NOW = new Date('2026-01-01T12:00:00Z');
function blankPerson(dob = '1961-01-01'): Person {
  return { dob, retirementAge: 65, planEnd: '2035-12-31', income: 0,
    pension: 0, cppPercent: 0, cppAge: 65, oasPercent: 0, oasDeferral: 0,
    accounts: Object.fromEntries(ACCOUNTS.map(t => [t, { balance: 0, contribution: 0, indexed: false }])) as Person['accounts'] };
}
function scenario(): Scenario {
  return { client: blankPerson(), spouse: blankPerson('1966-01-01'), hasSpouse: false,
    beforeReturn: 0, retirementReturn: 0, inflation: 0, order: [...ACCOUNTS] };
}

describe('annual investment and retirement timing', () => {
  it('contributes before growth, with no contribution in the retirement year', () => {
    const s = scenario(); s.client.dob = '1986-01-01'; s.client.retirementAge = 42;
    s.beforeReturn = 10; s.retirementReturn = 10;
    s.client.accounts.Cash = { balance: 100, contribution: 100, indexed: false };
    const p = project(s, NOW);
    expect(p.rows[0].total).toBeCloseTo(220);
    expect(p.rows[1].total).toBeCloseTo(352);
    expect(p.rows[2].contributions).toBe(0);
    expect(p.savingsAtRetirement).toBeCloseTo(352);
    expect(p.rows[2].total).toBeCloseTo(387.2);
  });
  it('withdraws before growth and honours a custom withdrawal order', () => {
    const s = scenario(); s.client.income = 50; s.retirementReturn = 10;
    s.client.accounts.Cash.balance = 100; s.client.accounts.TFSA.balance = 100;
    s.order = ['TFSA', 'Cash', 'RRSP'];
    const r = project(s, NOW).rows[0];
    expect(r.balances.Cash).toBeCloseTo(110);
    expect(r.balances.TFSA).toBeCloseTo(55);
    expect(r.draw).toBe(50);
  });
  it('indexes contributions only when selected, and targets the current-income baseline', () => {
    const s = scenario(); s.client.dob = '1986-01-01'; s.client.retirementAge = 42;
    s.inflation = 2; s.client.income = 100;
    s.client.accounts.Cash.contribution = 100;
    s.client.accounts.RRSP = { balance: 0, contribution: 100, indexed: true };
    const p = project(s, NOW);
    expect(p.rows[0].contributions).toBe(200);
    expect(p.rows[1].contributions).toBe(202);
    expect(p.firstTarget).toBeCloseTo(104.04);
  });
  it('uses the current year as the baseline when opened after 2026', () => {
    const s = scenario(); s.client.income = 100; s.client.pension = 50; s.inflation = 5;
    const p = project(s, new Date('2028-10-01T12:00:00Z'));
    expect(p.rows[0].need).toBe(100);
    expect(p.rows[0].pension).toBe(50);
    expect(p.rows[1].pension).toBe(50);
    expect(p.rows[1].need).toBe(105);
    expect(p.alreadyRetired).toBe(true);
  });
  it('allows a negative return and never withdraws more than available', () => {
    const s = scenario(); s.retirementReturn = -20; s.client.income = 20;
    s.client.accounts.Cash.balance = 100;
    const p = project(s, NOW);
    expect(p.rows[0].total).toBe(64);
    expect(p.rows.at(-1)!.total).toBe(0);
    expect(p.rows.every(r => r.total >= 0)).toBe(true);
    expect(p.firstShortfall).toBeDefined();
  });
});

describe('separate retirements and household withdrawals', () => {
  it('counts working income and switches return rates separately', () => {
    const s = scenario(); s.hasSpouse = true; s.beforeReturn = 10;
    s.client.income = 100; s.spouse.income = 200; s.client.pension = 100;
    s.client.accounts.Cash.balance = 100; s.spouse.accounts.Cash.balance = 100;
    const p = project(s, NOW);
    expect(p.rows[0].need).toBe(300);
    expect(p.rows[0].employment).toBe(200);
    expect(p.rows[0].draw).toBe(0);
    expect(p.rows[0].total).toBe(210);
    const spouseRetirement = p.rows.find(r => r.year === 2031)!;
    expect(spouseRetirement.employment).toBe(0);
    expect(spouseRetirement.draw).toBe(200);
  });
  it('splits draws proportionally within account types before applying each return', () => {
    const s = scenario(); s.hasSpouse = true; s.beforeReturn = 100;
    s.client.income = 50; s.spouse.income = 50;
    s.client.accounts.Cash.balance = 300; s.spouse.accounts.Cash.balance = 100;
    const r = project(s, NOW).rows[0];
    expect(r.draw).toBe(50);
    // Client: 300 - 37.5. Spouse: (100 - 12.5) * 2.
    expect(r.total).toBe(437.5);
  });
  it('does not automatically invest employment or benefit income', () => {
    const s = scenario(); s.client.retirementAge = 70; s.client.cppPercent = 100;
    s.client.income = 100000;
    const r = project(s, NOW).rows[0];
    expect(r.employment).toBe(100000);
    expect(r.cpp).toBe(GOVERNMENT.cppAnnualMaximum);
    expect(r.total).toBe(0);
    expect(r.draw).toBe(0);
  });
});

describe('plan endpoints and survivor assumptions', () => {
  it('ends income after the endpoint year and transfers savings to the survivor', () => {
    const s = scenario(); s.hasSpouse = true;
    s.client.planEnd = '2027-06-30'; s.client.accounts.Cash.balance = 100;
    s.spouse.planEnd = '2033-12-31'; s.beforeReturn = 10;
    s.client.income = 10; s.client.pension = 10;
    s.spouse.income = 20;
    const p = project(s, NOW);
    expect(p.endYear).toBe(2033);
    expect(p.rows[1].need).toBe(30);
    expect(p.rows[1].pension).toBe(10);
    expect(p.rows[2].need).toBe(20);
    expect(p.rows[2].pension).toBe(0);
    expect(p.rows[2].ages[0]).toBeNull();
    expect(p.rows[2].total).toBeCloseTo(110); // Inherited savings use working survivor's rate.
    expect(p.rows[2].shortage).toBe(0);
  });
  it('stops each person’s government benefits and ends at the last endpoint', () => {
    const s = scenario(); s.hasSpouse = true; s.spouse.dob = '1961-01-01';
    s.client.planEnd = '2027-12-31'; s.spouse.planEnd = '2029-12-31';
    s.client.cppPercent = 100; s.spouse.cppPercent = 50;
    const p = project(s, NOW);
    expect(p.rows[1].cpp).toBe(GOVERNMENT.cppAnnualMaximum * 1.5);
    expect(p.rows[2].cpp).toBe(GOVERNMENT.cppAnnualMaximum * 0.5);
    expect(p.rows.at(-1)!.year).toBe(2029);
  });
});

describe('government benefit calculations', () => {
  it('prorates start birthdays by exact days including the birthday', () => {
    expect(birthdayFraction('1961-12-31', 65, 2026)).toBeCloseTo(1 / 365);
    expect(birthdayFraction('1959-06-30', 65, 2024)).toBeCloseTo(185 / 366);
    expect(birthdayFraction('1960-02-29', 65, 2025)).toBeCloseTo(307 / 365);
    expect(birthdayFraction('1961-01-01', 65, 2025)).toBe(0);
    expect(birthdayFraction('1961-01-01', 65, 2027)).toBe(1);
  });
  it('applies CPP early and late adjustments and OAS deferral', () => {
    const p = blankPerson('1956-01-01'); p.cppPercent = 100; p.oasPercent = 100;
    p.cppAge = 60;
    expect(benefit(p, 'cpp', 2026, 0)).toBeCloseTo(GOVERNMENT.cppAnnualMaximum * .64);
    p.cppAge = 70;
    expect(benefit(p, 'cpp', 2026, 0)).toBeCloseTo(GOVERNMENT.cppAnnualMaximum * 1.42);
    p.oasDeferral = 5;
    expect(benefit(p, 'oas', 2026, 0)).toBeCloseTo(GOVERNMENT.oasAnnualMaximum * 1.36);
  });
  it('indexes from the benefit reference year, not the projection opening year', () => {
    const p = blankPerson(); p.cppPercent = 100;
    expect(benefit(p, 'cpp', 2028, 2)).toBeCloseTo(GOVERNMENT.cppAnnualMaximum * 1.02 ** 2);
  });
});

describe('verdicts and validation', () => {
  it('can be funded with zero savings', () => {
    const s = scenario(); s.client.income = 100; s.client.pension = 100;
    const p = project(s, NOW);
    expect(p.finalBalance).toBe(0); expect(p.firstShortfall).toBeUndefined();
    expect(p.fundedYears).toBe(p.retirementYearsCount);
  });
  it('preserves a first shortfall even if later years are fully funded', () => {
    const s = scenario(); s.client.dob = '1962-01-01'; s.client.retirementAge = 64;
    s.client.income = 1000; s.client.cppPercent = 100;
    const p = project(s, NOW);
    expect(p.firstShortfall?.year).toBe(2026);
    expect(p.fundedYears).toBe(p.retirementYearsCount - 1);
    expect(p.rows[1].shortage).toBe(0);
  });
  it('rejects invalid inputs instead of producing a misleading projection', () => {
    const s = scenario(); s.client.income = NaN; s.order = ['Cash', 'Cash', 'TFSA'];
    s.client.cppAge = 59; s.client.planEnd = '2026-02-30';
    const errors = validate(s, NOW);
    expect(errors['client.income']).toBeTruthy(); expect(errors['client.cppAge']).toBeTruthy();
    expect(errors['client.planEnd']).toBeTruthy(); expect(errors.order).toBeTruthy();
    expect(() => project(s, NOW)).toThrow();
  });
  it('ignores an excluded spouse and supplies a valid example', () => {
    const s = defaultScenario(NOW); s.spouse.income = NaN;
    expect(validate(s, NOW)).toEqual({});
    expect(project(s, NOW).rows.every(r => Number.isFinite(r.total))).toBe(true);
  });
  it('shows actual current age separately from calendar-year age', () => {
    expect(currentAge('1981-06-15', NOW)).toBe(44);
    const s = scenario(); s.client.dob = '1981-06-15'; s.client.retirementAge = 45;
    expect(project(s, NOW).rows[0].ages[0]).toBe(45);
  });
});
