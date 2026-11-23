import { expect, test, type Locator, type Page } from '@playwright/test';

// The fixture (src/lib/fixtures/plan.jsonl) is a recorded `plan-edit --json` run: a plan with
// 15 rows (5 uploads, 3 deletes, 3 already on the device, 2 used, 1 protected, 1 missing),
// after `--exclude 8` turned one delete off.
const rows = (page: Page) => page.locator('tbody tr');
const box = async (l: Locator) => {
  const b = await l.boundingBox();
  if (!b) throw new Error(`${l} isn't drawn`);
  return b;
};

test('the plan lists every row with its totals', async ({ page }) => {
  const errors: string[] = [];
  page.on('pageerror', (e) => errors.push(e.message));
  await page.goto('/plan');
  await expect(rows(page)).toHaveCount(15);
  await expect(page.getByText('upload 5 files (405 KB) into 5 folders, delete 2 (186 KB), 1 excluded, about 33 s')).toBeVisible();
  const excluded = rows(page).filter({ hasText: 'HH_CL_OLD' });
  await expect(excluded).toContainText('excluded-delete');
  const used = rows(page).filter({ hasText: 'HH_OP_VINTAGE' });
  await expect(used).toContainText('same content hash as a sample a project uses');
  expect(errors).toEqual([]);
});

test('the flow sizes each action by bytes and filters on click', async ({ page }) => {
  await page.goto('/plan');
  const flow = page.getByRole('region', { name: 'Flow' });
  const band = (name: RegExp) => box(flow.getByRole('button', { name }));
  // Both flows share one scale: the export's 623,000 bytes, the larger of the two.
  const [all, upload, skip, del, used] = await Promise.all([
    box(flow.getByRole('group', { name: 'Export to device' })),
    band(/^upload/), band(/^skip-exists/), band(/^delete/), band(/^keep-used/)
  ]);
  expect(upload.width / all.width).toBeCloseTo(415000 / 623000, 2);
  expect(skip.width / all.width).toBeCloseTo(208000 / 623000, 2);
  expect(del.width / all.width).toBeCloseTo(190000 / 623000, 2);
  expect(used.width / all.width).toBeCloseTo(300000 / 623000, 2);
  // A missing file has no bytes, so it has no band; it's still in the list.
  await expect(flow.getByRole('button', { name: /^skip-missing/ })).toHaveCount(0);

  await flow.getByRole('button', { name: /^keep-used/ }).click();
  await expect(rows(page)).toHaveCount(2);
  await flow.getByRole('button', { name: /^keep-used/ }).click();
  await expect(rows(page)).toHaveCount(15);
});
