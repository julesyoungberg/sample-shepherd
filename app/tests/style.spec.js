import { expect, test } from '@playwright/test';

const sections = ['Surfaces', 'Type', 'Categories', 'Buttons', 'Inputs', 'Table', 'Waveform'];

// WCAG relative luminance and contrast ratio for "rgb(r, g, b)" strings.
function luminance(rgb) {
  const [r, g, b] = rgb.match(/\d+/g).slice(0, 3).map((v) => {
    const c = Number(v) / 255;
    return c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4;
  });
  return 0.2126 * r + 0.7152 * g + 0.0722 * b;
}
function contrast(a, b) {
  const [hi, lo] = [luminance(a), luminance(b)].sort((x, y) => y - x);
  return (hi + 0.05) / (lo + 0.05);
}

test('the style sheet shows every section without errors', async ({ page }) => {
  const errors = [];
  page.on('pageerror', (e) => errors.push(e.message));
  page.on('console', (m) => m.type() === 'error' && errors.push(m.text()));
  await page.goto('/dev/style');
  for (const name of sections) {
    await expect(page.getByRole('heading', { name: new RegExp(name) })).toBeVisible();
  }
  // Each waveform canvas has drawn something.
  const drawn = await page.locator('canvas').evaluateAll((canvases) =>
    canvases.map((c) => c.getContext('2d').getImageData(0, 0, c.width, c.height).data.some((v) => v !== 0))
  );
  expect(drawn).toEqual([true, true]);
  expect(errors).toEqual([]);
});

test('the app opens in Console, the dark theme, even when the OS is light', async ({ page }) => {
  await page.emulateMedia({ colorScheme: 'light' });
  await page.goto('/library');
  const background = () => page.evaluate(() => getComputedStyle(document.documentElement).backgroundColor);
  expect(await background()).toBe('rgb(18, 17, 16)');
  await page.goto('/dev/style');
  await page.getByRole('button', { name: 'Paper' }).click();
  expect(await background()).toBe('rgb(243, 240, 232)');
});

// Category colors mark table rows, waveforms and maps, so they must stand out from the
// background in both themes (WCAG asks 3:1 for graphics).
for (const theme of ['Paper', 'Console']) {
  test(`category colors reach 3:1 contrast in ${theme}`, async ({ page }) => {
    await page.goto('/dev/style');
    await page.getByRole('button', { name: theme }).click();
    const paper = await page.evaluate(() => getComputedStyle(document.documentElement).backgroundColor);
    const swatches = await page.locator('[data-category]').evaluateAll((els) =>
      els.map((el) => [el.dataset.category, getComputedStyle(el).backgroundColor])
    );
    expect(swatches).toHaveLength(10);
    // An undefined token renders transparent ("rgba(0, 0, 0, 0)"), which would pass the contrast check.
    expect(swatches.filter(([, color]) => !color.startsWith('rgb('))).toEqual([]);
    const low = swatches.filter(([, color]) => contrast(color, paper) < 3).map(([cat]) => cat);
    expect(low).toEqual([]);
  });
}
