import { expect, test } from '@playwright/test';

// The fixture (src/lib/fixtures/library-ls.jsonl) is a recorded `library ls --json` run: 23 samples.
const rows = (page) => page.locator('tbody tr');

test('the library lists every sample from the CLI rows', async ({ page }) => {
  const errors = [];
  page.on('pageerror', (e) => errors.push(e.message));
  await page.goto('/library');
  await expect(rows(page)).toHaveCount(23);
  await expect(page.getByText('23 of 23 samples')).toBeVisible();
  const kick = rows(page).filter({ hasText: 'KICK_TAPE_01.wav' });
  await expect(kick).toContainText('KICKS');
  await expect(kick).toContainText('keep');
  expect(errors).toEqual([]);
});

test('filters narrow the table and combine', async ({ page }) => {
  await page.goto('/library');
  await page.getByLabel('Filter').fill('kick');
  await expect(rows(page)).toHaveCount(5);
  await page.getByLabel('Channels').selectOption('stereo');
  await expect(page.getByText('No samples match these filters.')).toBeVisible();
  await page.getByLabel('Filter').fill('');
  await page.getByLabel('Rating').selectOption('unrated');
  await expect(rows(page)).toHaveCount(5);
});

test('a folder shows its samples and its subfolders', async ({ page }) => {
  await page.goto('/library');
  const folders = page.getByRole('navigation', { name: 'Folders' });
  await folders.getByRole('button', { name: /^01_KICKS/ }).click();
  await expect(rows(page)).toHaveCount(5);
  await folders.getByRole('button', { name: /^Acoustic/ }).click();
  await expect(rows(page)).toHaveCount(3);
  // Uncategorized samples still list, without a color.
  await folders.getByRole('button', { name: /^UNSORTED/ }).click();
  await expect(rows(page)).toHaveCount(1);
  await expect(rows(page)).toContainText('mystery take 4.wav');
});
