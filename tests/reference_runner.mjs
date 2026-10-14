// Node is a verification dependency only. Execute the exact recovered source.
import { project } from '../original_fresh/src/model.ts';
import { stripTypeScriptTypes } from 'node:module';
import { readFileSync } from 'node:fs';

const source = readFileSync(new URL('../original_fresh/src/model.ts', import.meta.url), 'utf8');
const oldExpression = 'p.accounts[type].contribution * (p.accounts[type].indexed ? inflationFactor : 1)';
const newExpression = 'p.accounts[type].contribution * Math.pow(1 + p.accounts[type].indexationPercent / 100, year - startYear)';
if (source.split(oldExpression).length !== 2) throw Error('Reference expression changed; review verification adapter');
// Separate oracle for the approved contribution formula. Original files stay intact.
const extension = stripTypeScriptTypes(source.replace(oldExpression, newExpression));
const numeric = await import('data:text/javascript;base64,' + Buffer.from(extension).toString('base64'));
const gapExpression = 'let remaining = retired ? Math.max(0, need - employment - pension - cpp - oas) : 0;';
if (source.split(gapExpression).length !== 2) throw Error('Reference funding expression changed');
// Independently extend the old fixed-pension engine for cases with income excess.
// Cases without excess continue to compare every field with the untouched engine.
const savingBlock = `
    const saved = retired ? Math.max(0, employment + pension + cpp + oas - need) : 0;
    if (saved > 0) {
      const excesses = people.map((p,i) => active[i] ? Math.max(0,
        (year < retirementYears[i] ? p.income * inflationFactor : p.pension)
        + benefit(p,'cpp',year,s.inflation) + benefit(p,'oas',year,s.inflation)
        - p.income * inflationFactor) : 0);
      const totalExcess = excesses.reduce((n,value) => n + value,0);
      if (!Number.isFinite(totalExcess) || totalExcess <= 0) throw Error('Cannot allocate surplus');
      excesses.forEach((value,i) => {balances[i].Cash += saved * (value / totalExcess);});
    }
`;
async function savedOracle(numericRates) {
  const text = (numericRates ? source.replace(oldExpression,newExpression) : source)
    .replace(gapExpression,gapExpression + savingBlock);
  return import('data:text/javascript;base64,' + Buffer.from(stripTypeScriptTypes(text)).toString('base64'));
}
const saving = await savedOracle(false), numericSaving = await savedOracle(true);
const cases = JSON.parse(readFileSync(0, 'utf8'));
const result = cases.map(c => {
  const calculate = c.numeric ? numeric.project : project;
  const date = new Date(c.as_of + 'T12:00:00Z');
  const legacy = calculate(c.scenario,date);
  const hasSurplus = legacy.rows.some(r => r.retired && r.employment + r.pension + r.cpp + r.oas > r.need);
  const projection = hasSurplus ? (c.numeric ? numericSaving : saving).project(c.scenario,date) : legacy;
  return {name:c.name,projection,surplus_saving:hasSurplus,
          legacy_final_balance_difference_cad:projection.finalBalance - legacy.finalBalance};
});
process.stdout.write(JSON.stringify(result));
