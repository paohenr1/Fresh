import {test,expect} from '@playwright/test';
import path from 'node:path';

test('dashboard edits, hidden indexation, nominal dollars and invalid inputs',async({page})=>{
  const errors:string[]=[];page.on('pageerror',e=>errors.push(e.message));
  await page.goto('/');
  await page.context().setOffline(true);
  await expect(page.locator('.metric-value').first()).toHaveText('$495,000');
  await expect(page.getByRole('button',{name:'Export advisor PDF'})).toBeEnabled();
  await expect(page.locator('.action-row .button-primary')).toHaveText(['Export advisor PDF','Export client PDF']);
  await expect(page.getByLabel('Dollar basis')).toHaveCount(0);
  await expect(page.getByLabel('Client RRSP annual contribution increase')).toBeHidden();
  await page.locator('.account-group').nth(1).locator('summary').click();
  await page.getByLabel('Client RRSP annual contribution increase').fill('3.75');
  await expect(page.locator('.account-group').nth(1).locator('summary')).toHaveText('Edit indexation · 3.75%/year');
  await page.locator('.account-group').nth(1).locator('summary').click();
  await expect(page.getByLabel('Client RRSP annual contribution increase')).toBeHidden();
  await page.getByRole('button',{name:'03 Pension & benefits'}).click();
  const pension=page.locator('.input-card').nth(2);
  await pension.locator('summary').click();
  await page.getByLabel('Client Annual pension increase',{exact:true}).fill('2.5');
  await expect(pension.locator('summary')).toHaveText('Edit indexation · 2.5%/year');
  await page.getByRole('button',{name:/Your year-by-year projection/}).click();
  const firstPension=page.locator('tbody tr').first().locator('td').nth(7);
  await expect(firstPension).toHaveText('$18,000');
  await expect(page.locator('tbody tr').nth(1).locator('td').nth(7)).toHaveText('$18,450');
  await page.getByLabel('Client Annual pension increase',{exact:true}).fill('-101');
  await expect(page.getByRole('button',{name:'Export advisor PDF'})).toBeDisabled();
  await expect(page.locator('.validation-state')).toBeVisible();
  await page.getByRole('button',{name:'Reset example'}).click();
  await expect(page.getByRole('button',{name:'Export advisor PDF'})).toBeEnabled();
  expect(errors).toEqual([]);
  await page.screenshot({path:'../tmp/browser-dashboard.png',fullPage:true});
});

test('both PDF exports use current indexed inputs in nominal CAD',async({page})=>{
  await page.goto('/');
  await page.context().setOffline(true);
  await page.getByRole('button',{name:'03 Pension & benefits'}).click();
  await page.locator('.input-card').nth(2).locator('summary').click();
  await page.getByLabel('Client Annual pension increase',{exact:true}).fill('2.5');
  await page.getByRole('button',{name:/Your year-by-year projection/}).click();
  await expect(page.getByLabel('Dollar basis')).toHaveCount(0);
  for(const kind of ['client','advisor']){
    const promise=page.waitForEvent('download');
    await page.getByRole('button',{name:`Export ${kind} PDF`}).click();
    const download=await promise;
    expect(await download.failure()).toBeNull();
    await download.saveAs(path.resolve(`../output/pdf/fresh-browser-${kind}.pdf`));
  }
});

test('long retirement tables export with continuation pages',async({page})=>{
  await page.goto('/');
  await page.getByRole('switch',{name:'Include spouse'}).click();
  await page.locator('.date-edit').first().locator('summary').click();
  await page.getByLabel('Client Birth date',{exact:true}).fill('1981-06-15');
  await page.locator('.date-edit').nth(1).locator('summary').click();
  await page.getByLabel('Client End date',{exact:true}).fill('2076-12-31');
  await expect(page.getByRole('button',{name:'Export advisor PDF'})).toBeEnabled();
  const promise=page.waitForEvent('download');
  await page.getByRole('button',{name:'Export advisor PDF'}).click();
  const download=await promise;
  expect(await download.failure()).toBeNull();
  await download.saveAs(path.resolve('../tmp/pdfs/fresh-browser-long-advisor.pdf'));
});

test('date editors retain exact dates and narrow layouts remain usable',async({page})=>{
  await page.setViewportSize({width:390,height:844});await page.goto('/');
  await expect(page.getByLabel('Client Current age',{exact:true})).toHaveValue('65');
  await page.locator('.date-edit').first().locator('summary').click();
  await page.getByLabel('Client Birth date',{exact:true}).fill('1961-12-31');
  await expect(page.getByLabel('Client Current age',{exact:true})).toHaveValue('64');
  await expect(page.getByRole('button',{name:'Export advisor PDF'})).toBeEnabled();
  await expect(page.locator('svg[data-chart="balance"] polygon').nth(1)).toBeVisible();
  expect(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth)).toBe(true);
  await page.screenshot({path:'../tmp/browser-mobile.png',fullPage:true});
});
