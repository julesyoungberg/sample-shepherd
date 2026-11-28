import { expect, test, type Locator, type Page } from '@playwright/test';

// The fixture (src/lib/fixtures/library-ls.jsonl) is a recorded `library ls --json` run: 24 samples.
const rows = (page: Page) => page.locator('tbody tr');

test('the library lists every sample from the CLI rows', async ({ page }) => {
  const errors: string[] = [];
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
  const box = async (l: Locator) => {
    const b = await l.boundingBox();
    if (!b) throw new Error(`${l} isn't drawn`);
    return b;
  };
  const band = (name: string) => box(terrain.getByRole('button', { name, exact: true }));
  const [all, drums, kicks, acoustic] = await Promise.all([box(terrain), band('DRUMS'), band('01_KICKS'), band('Acoustic')]);
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

// In the desktop window the screen asks the Tauri shell to run `library ls`. Stand in for the shell's invoke.
const shell = (page: Page, answer: { stream?: string; reject?: string }) =>
  page.addInitScript((a) => {
    (window as any).__TAURI__ = { core: { invoke: async () => (a.reject ? Promise.reject(a.reject) : a.stream) } };
  }, answer);

test('in the desktop window the library comes from the CLI', async ({ page }) => {
  const row = { v: 1, type: 'row', kind: 'sample', path: 'KICKS/LIVE.wav', folder: 'KICKS', category: 'KICKS',
    duration: 0.5, sample_rate: 44100, channels: 1, size: 44144, sha256: 'x', rating: null };
  const result = { v: 1, type: 'result', ok: true, exit: 0, summary: { samples: 1 } };
  await shell(page, { stream: [row, result].map((e) => JSON.stringify(e)).join('\n') });
  await page.goto('/library');
  await expect(rows(page)).toHaveCount(1);
  await expect(rows(page)).toContainText('LIVE.wav');
});

test("the CLI's error, or why it couldn't run or finish, shows on the screen", async ({ page }) => {
  const error = { v: 1, type: 'error', code: 'user_error', msg: 'no library index yet: run library index', exit: 2 };
  await shell(page, { stream: JSON.stringify(error) + '\n' });
  await page.goto('/library');
  await expect(page.getByRole('alert')).toHaveText('no library index yet: run library index');

  const other = await page.context().newPage();
  await shell(other, { reject: "couldn't run sample-shepherd: not found" });
  await other.goto('/library');
  await expect(other.getByRole('alert')).toHaveText("couldn't run sample-shepherd: not found");
  await expect(rows(other)).toHaveCount(0);

  const killed = await page.context().newPage();
  const row = { v: 1, type: 'row', kind: 'sample', path: 'A.wav', folder: '', category: null,
    duration: 1, sample_rate: 44100, channels: 1, size: 1, sha256: 'x', rating: null };
  await shell(killed, { stream: JSON.stringify(row) + '\n' });
  await killed.goto('/library');
  await expect(killed.getByRole('alert')).toHaveText('sample-shepherd stopped before it finished');
});
