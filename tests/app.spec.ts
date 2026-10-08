import { test, expect } from '@playwright/test';
import fs from 'node:fs/promises';

test.beforeEach(async ({ page }) => {
  await page.clock.setFixedTime(new Date('2026-10-07T12:00:00Z'));
});

test('recalculates live, validates input, and supports independent spouse fields', async ({ page }) => {
  const errors: string[] = [];
  page.on('pageerror', e => errors.push(e.message));
  await page.goto('/');
  await expect(page.getByRole('heading', { name: 'Your future, in perspective.' })).toBeVisible();
  await expect(page.getByTestId('verdict')).toBeVisible();
  const first = await page.getByTestId('verdict').innerText();
  await page.getByRole('spinbutton', { name: 'Client Current income', exact: true }).fill('900000');
  await expect(page.getByTestId('verdict')).toContainText('Shortfall in this scenario');
  expect(await page.getByTestId('verdict').innerText()).not.toBe(first);
  await page.getByRole('spinbutton', { name: 'Client Current income', exact: true }).fill('-1');
  await expect(page.getByRole('button', { name: 'Export client PDF' })).toBeDisabled();
  await expect(page.getByRole('alert')).toContainText('Correct the highlighted fields');
  await page.getByRole('spinbutton', { name: 'Client Current income', exact: true }).fill('65000');
  await page.getByRole('switch', { name: 'Include spouse' }).click();
  await page.getByRole('tab', { name: 'Spouse', exact: true }).click();
  await page.getByRole('spinbutton', { name: 'Spouse Retirement age', exact: true }).fill('62');
  await page.getByRole('spinbutton', { name: 'Spouse Current income', exact: true }).fill('42000');
  await page.getByRole('button', { name: /Your year-by-year projection/ }).click();
  await expect(page.getByRole('columnheader', { name: 'Spouse age' })).toBeVisible();
  await expect(page.locator('tbody tr')).toHaveCount(54);
  await page.getByRole('tab', { name: 'You', exact: true }).click();
  await expect(page.getByRole('spinbutton', { name: 'Client Current income', exact: true })).toHaveValue('65000');
  await page.getByRole('switch', { name: 'Include spouse' }).click();
  await expect(page.getByRole('columnheader', { name: 'Spouse age' })).toHaveCount(0);
  expect(errors).toEqual([]);
});

test('exports a complete PDF twice, reflecting the updated scenario', async ({ page }, testInfo) => {
  await page.goto('/');
  const firstDownload = page.waitForEvent('download');
  await page.getByRole('button', { name: 'Export client PDF' }).click();
  const first = await firstDownload;
  expect(first.suggestedFilename()).toBe('fresh-client-retirement-projection.pdf');
  const firstPath = testInfo.outputPath('first.pdf'); await first.saveAs(firstPath);
  const firstBytes = await fs.readFile(firstPath);
  expect(firstBytes.subarray(0, 5).toString()).toBe('%PDF-');
  expect(firstBytes.toString('latin1')).toContain('/Subtype /Image');
  expect(firstBytes.toString('latin1')).toContain('Your year-by-year projection');
  expect(firstBytes.toString('latin1')).toContain('2076');
  await page.getByRole('spinbutton', { name: 'Client Current income', exact: true }).fill('900000');
  const nextDownload = page.waitForEvent('download');
  await page.getByRole('button', { name: 'Export client PDF' }).click();
  const next = await nextDownload;
  const nextPath = testInfo.outputPath('changed.pdf'); await next.saveAs(nextPath);
  const nextBytes = await fs.readFile(nextPath);
  expect(nextBytes.equals(firstBytes)).toBe(false);
  expect(nextBytes.toString('latin1')).toContain('SHORTFALL IN THIS SCENARIO');
  expect(nextBytes.toString('latin1')).toContain('900,000');
});

test('stays within a mobile viewport and makes no external requests', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  const external: string[] = [];
  page.on('request', r => { if (!r.url().startsWith('http://127.0.0.1:5173') && !r.url().startsWith('data:') && !r.url().startsWith('blob:')) external.push(r.url()); });
  await page.goto('/');
  await expect(page.getByTestId('verdict')).toBeVisible();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
  await page.getByRole('button', { name: /Your year-by-year projection/ }).click();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
  expect(external).toEqual([]);
});
