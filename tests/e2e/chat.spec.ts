import { test, expect } from '@playwright/test';

const AFIB_QUERY =
  'A 75-year-old female with atrial fibrillation and well-controlled hypertension needs stroke risk assessment.';

test('happy path: symptom query renders a recommendation with citations', async ({ page }) => {
  await page.goto('/');
  await page.fill('#query', AFIB_QUERY);
  await page.click('#submit');

  const result = page.locator('#result');
  await expect(result).toBeVisible({ timeout: 30_000 });
  // Semantic assertion: the right calculator concept, not an exact string
  await expect(page.locator('#calculator')).toHaveText(/CHA.?2?DS.?2|CHADS/i);
  await expect(page.locator('#rationale')).toContainText(/atrial fibrillation|stroke/i);
  await expect(page.locator('#citations li').first()).toBeVisible();
});

test('loading state shows while the request is in flight', async ({ page }) => {
  await page.route('**/api/recommend', async (route) => {
    await new Promise((resolve) => setTimeout(resolve, 1200));
    await route.continue();
  });

  await page.goto('/');
  await page.fill('#query', AFIB_QUERY);
  await page.click('#submit');

  await expect(page.locator('#loading')).toBeVisible();
  await expect(page.locator('#submit')).toBeDisabled();
  await expect(page.locator('#result')).toBeVisible({ timeout: 30_000 });
  await expect(page.locator('#loading')).toBeHidden();
});

test('error state: API failure surfaces a user-facing message, not a crash', async ({ page }) => {
  await page.route('**/api/recommend', (route) =>
    route.fulfill({ status: 500, contentType: 'application/json', body: '{"detail":"boom"}' }),
  );

  await page.goto('/');
  await page.fill('#query', AFIB_QUERY);
  await page.click('#submit');

  const error = page.locator('#error');
  await expect(error).toBeVisible();
  await expect(error).toContainText(/went wrong/i);
  await expect(page.locator('#result')).toBeHidden();
  // Form recovers for retry
  await expect(page.locator('#submit')).toBeEnabled();
});

test('decline path: pediatric query renders a decline, not a fabricated recommendation', async ({ page }) => {
  await page.goto('/');
  await page.fill(
    '#query',
    'A 5-year-old child presents with sudden onset dyspnea; the clinician requests a Wells PE score.',
  );
  await page.click('#submit');

  await expect(page.locator('#result')).toBeVisible({ timeout: 30_000 });
  await expect(page.locator('#calculator')).toHaveText(/no calculator/i);
  await expect(page.locator('#status-badge')).toHaveText('declined');
});
