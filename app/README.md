# Desktop app

The sample-shepherd desktop app: a SvelteKit single-page app that will run inside a Tauri
shell. The plan, stack and design direction are in
[docs/desktop-app-plan.md](../docs/desktop-app-plan.md).

What exists:

- The frontend scaffold: SvelteKit in SPA mode (`adapter-static`, `ssr = false`) and
  Tailwind v4.
- `/dev/style`, the style sheet: tokens, type, the category palette, buttons, inputs, a
  table and a waveform, in both themes (Console, the dark default, and Paper). Every
  later screen reuses these pieces.
- `/library`, the Library screen: folder tree, the terrain (folders as nested bands, each
  as wide as its share of the samples, colored by category), sample table, and filters by
  text, category, channels and rating. It reads a recorded `library ls --json` run until the sidecar exists.
- `/export`, the Export check: every issue `export check --json` found in a render, sorted
  by path, with the file and folder counts. It reads a recorded run until the sidecar exists.

- `src-tauri/`, the Tauri 2 shell: a native window that loads the built frontend. It has
  no Rust commands yet, so the screens still read recorded fixtures.

Not here yet: the CLI sidecar.

## Run it

```bash
cd app
pnpm install
pnpm exec playwright install chromium   # first time only, for pnpm test
pnpm dev        # http://localhost:5173/dev/style, reloads as you edit
pnpm check      # Svelte and TypeScript checks; fails on any type error
pnpm test       # Playwright: builds, serves on port 4173, runs tests/
```

### The desktop window (Tauri)

Needs Rust (`rustup`) and, on Linux, WebKitGTK and the other packages in
[Tauri's prerequisites](https://v2.tauri.app/start/prerequisites/). macOS needs only the
Xcode command line tools. The `sample-shepherd` cloud environment installs the Linux
packages in its setup script.

```bash
pnpm tauri dev                  # window on the dev server, reloads as you edit
pnpm tauri build --no-bundle    # release binary in src-tauri/target/release/
pnpm tauri build                # installers (.dmg, .deb, ...) in src-tauri/target/release/bundle/
```

On a Linux machine with no display, run the binary under Xvfb (`xvfb-run`).

## Where things are

- `src/app.css`: the design tokens (`@theme`), dark ("console", the default) and light
  ("paper") values, and the button and field styles.
- `src/lib/categories.ts`: the sample categories, in display order. Each has a
  `--color-cat-*` token.
- `src/lib/Waveform.svelte`: draws peaks on a canvas, one lane per channel.
- `src/routes/dev/style/+page.svelte`: the style sheet.
- `src/lib/events.ts`: types for the CLI's `--json` events, copied from
  `src/sample_shepherd/events.schema.json`. Change both together; a pytest
  (`tests/test_app_event_types.py`) fails when they differ.
- `src/lib/library.ts`: parses `library ls --json` rows, builds the folder tree, filters
  samples, lays out the terrain (`icicle`), and maps Fourier's categories (KICKS, PADS, ...) onto the palette.
- `src/lib/fixtures/library-ls.jsonl`: the recorded run, made by indexing a throwaway
  library of generated WAVs. Re-record it if the `sample` row changes.
- `src/routes/library/+page.svelte`: the Library screen.
- `src/lib/export.ts`: parses `export check --json` issues and the run's counts.
- `src/lib/fixtures/export-check.jsonl`: a recorded `export check --profile digitakt_2_50_3`
  run on a render of generated WAVs with one of each kind of issue. Re-record it if the
  `issue` row changes.
- `src/routes/export/+page.svelte`: the Export check screen.
- `tests/library.spec.ts`: the Library screen lists the fixture, its filters work, and
  the terrain sizes folders by sample count.
- `tests/export.spec.ts`: the Export check lists every issue in the fixture, sorted.
- `tests/style.spec.ts`: the style sheet renders, and every category color keeps 3:1
  contrast on both backgrounds (the WCAG minimum for graphics).
- `src-tauri/tauri.conf.json`: the window, the content security policy (only the app's
  own files; inline styles allowed because Svelte sets them) and the bundle icons.
- `src-tauri/capabilities/default.json`: what the webview may call in Rust. Only Tauri's
  core defaults for now.
- `src-tauri/icons/`: made from `static/favicon.svg` with `pnpm tauri icon static/favicon.svg`.
