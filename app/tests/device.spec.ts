import { expect, test, type Locator } from '@playwright/test';

// The fixtures: src/lib/fixtures/device-listing.jsonl, a recorded `device listing --json` run
// on the fake device holding the plan fixture's device files plus three outside any synced
// folder; plan.jsonl, which marks 2 used samples and 2 deletes among them; and
// device-info.jsonl, a recorded `device info` run on that fake device with a 4 MiB +Drive.
const box = async (l: Locator) => {
  const b = await l.boundingBox();
  if (!b) throw new Error(`${l} isn't drawn`);
  return b;
};

test('the map draws every sample, grouped by folder and sized by bytes', async ({ page }) => {
  const errors: string[] = [];
  page.on('pageerror', (e) => errors.push(e.message));
  await page.goto('/device');
  await expect(page.getByText('12 files, 1.3 MiB')).toBeVisible();
  const map = page.getByRole('region', { name: '+Drive map' });
  await expect(map.getByRole('img')).toHaveCount(12);
  await expect(map.getByRole('group')).toHaveCount(6);

  // Bars share one scale: recorded (440,013 bytes) is the largest folder.
  const bar = (name: string) => box(map.getByRole('group', { name }).locator('[data-bar]'));
  const [kicks, recorded] = await Promise.all([bar('01_KICKS'), bar('recorded')]);
  expect(kicks.width / recorded.width).toBeCloseTo(413983 / 440013, 2);
  // Inside a bar, each cell's width is its bytes.
  const hats = map.getByRole('group', { name: '04_HATS' });
  const [all, vintage] = await Promise.all([box(hats.locator('[data-bar]')), box(hats.getByRole('img', { name: /HH_OP_VINTAGE/ }))]);
  expect(vintage.width / all.width).toBeCloseTo(210022 / 264028, 2);
  expect(errors).toEqual([]);
});

test('samples a project uses and ones the plan deletes are marked', async ({ page }) => {
  await page.goto('/device');
  const map = page.getByRole('region', { name: '+Drive map' });
  await expect(map.getByRole('img', { name: /used by a project/ })).toHaveCount(2);
  await expect(map.getByRole('img', { name: /the plan deletes it/ })).toHaveCount(2);
  // An excluded delete stays on the device, so it isn't marked.
  await expect(map.getByRole('img', { name: '/04_HATS/Closed/HH_CL_OLD, 29 KiB' })).toBeVisible();
});

test("the space strip shows each folder's share of the drive and the free space", async ({ page }) => {
  await page.goto('/device');
  await expect(page.getByText('1.3 MiB used of 4.0 MiB, 2.7 MiB free')).toBeVisible();
  const strip = page.getByRole('img', { name: '+Drive space: 2.7 MiB free' });
  const [all, recorded] = await Promise.all([box(strip), box(strip.locator('[data-folder="recorded"]'))]);
  expect(recorded.width / all.width).toBeCloseTo(440013 / 4194304, 2);
});
