import { expect, test } from '@playwright/test';

// The fixture (src/lib/fixtures/export-check.jsonl) is a recorded `export check --json` run
// on a Digitakt II render with 9 issues, sent in folder-walk order.
test('the export check lists every issue, sorted by path', async ({ page }) => {
  const errors = [];
  page.on('pageerror', (e) => errors.push(e.message));
  await page.goto('/export');
  const rows = page.locator('tbody tr');
  await expect(rows).toHaveCount(9);
  await expect(page.getByText('59 files in 5 folders, 9 issues')).toBeVisible();
  await expect(rows.first()).toContainText('01_KICKS/Acoustic');
  await expect(rows.first()).toContainText('52 files, profile allows 50');
  await expect(rows.last()).toContainText('not a readable WAV');
  expect(errors).toEqual([]);
});
