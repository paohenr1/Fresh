// Node is a verification dependency only. Execute the exact recovered source.
import { project } from '../original_fresh/src/model.ts';
import { stripTypeScriptTypes } from 'node:module';
import { readFileSync } from 'node:fs';

const source = readFileSync(new URL('../original_fresh/src/model.ts', import.meta.url), 'utf8');
const oldExpression = 'p.accounts[type].contribution * (p.accounts[type].indexed ? inflationFactor : 1)';
const newExpression = 'p.accounts[type].contribution * Math.pow(1 + p.accounts[type].indexationPercent / 100, year - startYear)';
if (source.split(oldExpression).length !== 2) throw Error('Reference expression changed; review verification adapter');
// This separate oracle changes only the specifically authorized formula. Legacy
// parity always calls the untouched source project(), not this modified oracle.
const extension = stripTypeScriptTypes(source.replace(oldExpression, newExpression));
const numeric = await import('data:text/javascript;base64,' + Buffer.from(extension).toString('base64'));
const cases = JSON.parse(readFileSync(0, 'utf8'));
const result = cases.map(c => {
  const calculate = c.numeric ? numeric.project : project;
  return {name: c.name, projection: calculate(c.scenario, new Date(c.as_of + 'T12:00:00Z'))};
});
process.stdout.write(JSON.stringify(result));
