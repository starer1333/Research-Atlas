const { test, expect } = require('@playwright/test');

test('research question becomes an evidence-linked claim and immutable revision', async ({ page }) => {
  await page.goto('/');
  await expect(page.locator('#companyName')).toContainText('NVIDIA');

  const firstResearchAction = page.locator('[data-action="research"]').first();
  await expect(firstResearchAction).toBeVisible();
  await firstResearchAction.click();
  await expect(page.locator('#toast')).toContainText('研究问题已保存');

  await page.locator('[data-page="report"]').first().click();
  await expect(page.locator('[data-claim-workspace]')).toBeVisible();
  await expect(page.locator('#claimForm')).toBeVisible();

  await page.locator('textarea[name="conclusion"]').fill('Cash conversion remains strong, but working-capital expansion needs continued verification.');
  await page.locator('textarea[name="alternative"]').fill('Timing of collections and supplier payments may explain part of the cash relationship.');
  await page.locator('textarea[name="next_evidence"]').fill('If receivables continue to rise faster than revenue while CFO weakens, revisit this claim.');
  await page.locator('textarea[name="change_reason"]').fill('Initial evidence-linked claim from the selected research question.');
  await page.locator('select[name="status"]').selectOption('supported');

  const support = page.locator('input[name="supporting"]');
  const counter = page.locator('input[name="counter"]');
  await expect(support.first()).toBeVisible();
  if (!(await support.first().isChecked())) await support.first().check();
  const counterIndex = (await counter.count()) > 1 ? 1 : 0;
  if (!(await counter.nth(counterIndex).isChecked())) await counter.nth(counterIndex).check();
  if (await support.nth(counterIndex).isChecked()) await support.nth(counterIndex).uncheck();

  await page.locator('#claimForm button[type="submit"]').click();
  await expect(page.locator('.current-claim')).toContainText('Cash conversion remains strong');
  await expect(page.locator('.claim-history article')).toHaveCount(1);

  await page.locator('textarea[name="conclusion"]').fill('Cash conversion is still supportive, but the claim is now challenged by working-capital intensity.');
  await page.locator('textarea[name="change_reason"]').fill('Counter-evidence received more weight in the revised judgment.');
  await page.locator('select[name="status"]').selectOption('challenged');
  await page.locator('#claimForm button[type="submit"]').click();

  await expect(page.locator('.current-claim')).toContainText('now challenged');
  await expect(page.locator('.claim-history article')).toHaveCount(2);
  await expect(page.locator('.claim-history')).toContainText('prior revision');
});

test('evidence drawer exposes the unified provenance envelope', async ({ page }) => {
  await page.goto('/');
  const evidenceButton = page.locator('[data-action="evidence"]').first();
  await evidenceButton.click();
  await expect(page.locator('#evidenceDrawer')).toBeVisible();
  await expect(page.locator('#drawerBody')).toContainText('Source type');
  await expect(page.locator('#drawerBody')).toContainText('Locator');
  await expect(page.locator('#drawerBody')).toContainText('Source tag');
  await expect(page.locator('#drawerBody')).toContainText('Extraction');
});

test('primary navigation reaches all four research stages', async ({ page }) => {
  await page.goto('/');
  for (const stage of ['evidence','analysis','report','research']) {
    await page.locator('[data-page="'+stage+'"]').first().click();
    await expect(page.locator('#content')).toBeVisible();
  }
});
