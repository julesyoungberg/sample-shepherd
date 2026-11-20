import { expect, test } from '@playwright/test';

// The fixture (src/lib/fixtures/library-ls.jsonl) is a recorded `library ls --json` run: 24 samples.
const rows = (page) => page.locator('tbody tr');

test('the library lists every sample from the CLI rows', async ({ page }) => {
  const errors = [];
  page.on('pageerror', (e) => errors.push(e.message));
  await page.goto('/library');
  await expect(rows(page)).toHaveCount(24);
  await expect(page.getByText('24 of 24 samples')).toBeVisible();
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
  // Uncategorized samples still list, without a color swatch.
  await folders.getByRole('button', { name: /^UNSORTED/ }).click();
  await expect(rows(page)).toHaveCount(1);
  await expect(rows(page)).toContainText('mystery take 4.wav');
  await expect(rows(page).locator('span')).toHaveCount(0);
});

test('each folder follows its parent, even when a sibling name sorts before "/"', async ({ page }) => {
  await page.goto('/library');
  const folders = page.getByRole('navigation', { name: 'Folders' });
  // evaluateAll doesn't wait, so wait for the tree to be drawn first.
  await expect(folders.getByRole('button', { name: /^DRUMS EXTRA/ })).toBeVisible();
  const names = await folders.getByRole('button').evaluateAll((els) =>
    els.map((el) => el.querySelector('span')?.textContent).filter(Boolean)
  );
  // "DRUMS EXTRA" sorts before "DRUMS/01_KICKS" as a plain string, which would draw DRUMS's subfolders under it.
  expect(names.slice(names.indexOf('DRUMS'), names.indexOf('FX'))).toEqual([
    'DRUMS', '01_KICKS', 'Acoustic', 'Electronic', '02_SNARES', '03_CLAPS', '04_HATS', 'Closed', 'Open', '07_PERC', 'DRUMS EXTRA'
  ]);
});

test('the terrain sizes each folder by its samples and filters on click', async ({ page }) => {
  await page.goto('/library');
  const terrain = page.getByRole('region', { name: 'Terrain' });
  const box = (name) => terrain.getByRole('button', { name, exact: true }).boundingBox();
  const [all, drums, kicks, acoustic] = await Promise.all([terrain.boundingBox(), box('DRUMS'), box('01_KICKS'), box('Acoustic')]);
  // 13 of 24 samples are under DRUMS, 5 under its 01_KICKS, 3 under that folder's Acoustic.
  expect(drums.width / all.width).toBeCloseTo(13 / 24, 2);
  expect(kicks.width / all.width).toBeCloseTo(5 / 24, 2);
  expect(acoustic.width / all.width).toBeCloseTo(3 / 24, 2);
  // Each folder sits inside its parent's span, one band lower.
  expect(kicks.x).toBeGreaterThanOrEqual(drums.x);
  expect(kicks.x + kicks.width).toBeLessThanOrEqual(drums.x + drums.width + 0.5);
  expect(kicks.y).toBeGreaterThan(drums.y);

  await terrain.getByRole('button', { name: '01_KICKS', exact: true }).click();
  await expect(rows(page)).toHaveCount(5);
  // A second click clears the folder filter.
  await terrain.getByRole('button', { name: '01_KICKS', exact: true }).click();
  await expect(rows(page)).toHaveCount(24);
});
