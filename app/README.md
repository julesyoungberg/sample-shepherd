# Desktop app

The sample-shepherd desktop app: a SvelteKit single-page app that will run inside a Tauri
shell. The plan, stack and design direction are in
[docs/desktop-app-plan.md](../docs/desktop-app-plan.md).

What exists:

- The frontend scaffold: SvelteKit in SPA mode (`adapter-static`, `ssr = false`) and
  Tailwind v4.
- `/dev/style`, the style sheet: tokens, type, the category palette, buttons, inputs, a
  table and a waveform, in both themes. Every later screen reuses these pieces.
- `/library`, the Library screen: folder tree, the terrain (folders as nested bands, each
  as wide as its share of the samples, colored by category), sample table, and filters by
  text, category, channels and rating. It reads a recorded `library ls --json` run until the sidecar exists.

Not here yet: the Tauri shell (`src-tauri/`) and the CLI sidecar.

## Run it

```bash
cd app
pnpm install
pnpm exec playwright install chromium   # first time only, for pnpm test
pnpm dev        # http://localhost:5173/dev/style, reloads as you edit
pnpm check      # Svelte and type checks
pnpm test       # Playwright: builds, serves on port 4173, runs tests/
```

## Where things are

- `src/app.css`: the design tokens (`@theme`), light ("paper") and dark ("console") values,
  and the button and field styles.
- `src/lib/categories.js`: the sample categories, in display order. Each has a
  `--color-cat-*` token.
- `src/lib/Waveform.svelte`: draws peaks on a canvas, one lane per channel.
- `src/routes/dev/style/+page.svelte`: the style sheet.
- `src/lib/library.js`: parses `library ls --json` rows, builds the folder tree, filters
  samples, lays out the terrain (`icicle`), and maps Fourier's categories (KICKS, PADS, ...) onto the palette.
- `src/lib/fixtures/library-ls.jsonl`: the recorded run, made by indexing a throwaway
  library of generated WAVs. Re-record it if the `sample` row changes.
- `src/routes/library/+page.svelte`: the Library screen.
- `tests/library.spec.js`: the Library screen lists the fixture, its filters work, and
  the terrain sizes folders by sample count.
- `tests/style.spec.js`: the style sheet renders, and every category color keeps 3:1
  contrast on both backgrounds (the WCAG minimum for graphics).
