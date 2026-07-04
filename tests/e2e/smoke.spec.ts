import { test, expect } from '@playwright/test';

test('landing page loads with query form', async ({ page }) => {
  await page.goto('/');
  await expect(page.locator('h1')).toHaveText('ClinCalc-Eval');
  await expect(page.locator('#query')).toBeVisible();
  await expect(page.locator('#submit')).toBeEnabled();
});
