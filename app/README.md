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
  text, category, channels and rating. In the desktop window it runs `library ls --json`;
  in a browser (`pnpm dev`, `pnpm test`) it reads a recorded run. The CLI's error shows
  above the table.
- `/export`, the Export check: every issue `export check --json` found in a render, sorted
  by path, with the file and folder counts. It reads a recorded run until the sidecar exists.
- `/plan`, the Sync plan: the plan's totals, two flows (the export into the device, and
  what's on the device to its fate) with each action as wide as its bytes, and every row
  and its reason. Clicking a band filters the rows. It reads a recorded run until the
  sidecar exists, so rows can't be excluded from here yet.

- `src-tauri/`, the Tauri 2 shell: a native window that loads the built frontend. Its one
  command, `library_ls`, runs `sample-shepherd --json library ls` and hands the events to
  the page (`src/lib/sidecar.ts`). Commands are named one by one, so the webview can only
  run read-only ones. The other screens still read recorded runs.

Not here yet: the PyInstaller sidecar. Until then the window runs `sample-shepherd` from
`PATH`, so install the CLI first (`uv pip install -e .` in the repo root, or `pipx`).

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
(cd src-tauri && cargo test)    # Rust tests: how a failed or missing CLI comes back
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
- `src/lib/plan.ts`: parses `plan --json` rows and totals, and lays out the flows.
- `src/lib/fixtures/plan.jsonl`: a recorded `plan-edit --exclude 8` run on a plan made with
  `--prune` and `--replace` from a hand-written listing and usage list and a render of
  empty files, so every action but `excluded-upload` shows up. Re-record it if the `plan`
  row changes.
- `src/routes/plan/+page.svelte`: the Sync plan screen.
- `src/lib/device.ts`: parses `device listing --json` rows, takes each sample's mark (used
  by a project, or deleted) from the plan's rows, and lays out the +Drive map. Reads the
  +Drive's size and free space from `device info --json`.
- `src/lib/fixtures/device-listing.jsonl`: a recorded `device listing` run on the fake
  device (`tests/fake/elektroid-cli`) holding the plan fixture's device files plus three
  outside any synced folder. Sizes are rounded as Elektroid prints them. Re-record it if the
  `listing` row changes.
- `src/lib/fixtures/device-info.jsonl`: a recorded `device info` run on that same fake
  device, with `FAKE_ELEKTROID_DRIVE_BYTES=4194304` (a 4 MiB +Drive) so free space shows.
- `src/routes/device/+page.svelte`: the Device screen's space strip (each folder's share of
  the drive, then free space) and +Drive map. Positioned elements for
  now; the plan's canvas comes when a full drive is too slow.
- `tests/library.spec.ts`: the Library screen lists the fixture, its filters work, and
  the terrain sizes folders by sample count. In a stand-in desktop window it shows what
  the CLI sent, or its error.
- `tests/export.spec.ts`: the Export check lists every issue in the fixture, sorted.
- `tests/plan.spec.ts`: the Sync plan lists every row with its totals, and the flow sizes
  actions by bytes and filters on click.
- `tests/device.spec.ts`: the +Drive map draws every sample sized by bytes and marks used
  and deleted ones; the space strip sizes folders against the drive's capacity.
- `tests/style.spec.ts`: the style sheet renders, and every category color keeps 3:1
  contrast on both backgrounds (the WCAG minimum for graphics).
- `src-tauri/tauri.conf.json`: the window, the content security policy (only the app's
  own files; inline styles allowed because Svelte sets them) and the bundle icons.
- `src-tauri/src/main.rs`: the Rust commands the webview may call (`library_ls`).
- `src-tauri/capabilities/default.json`: which of Tauri's own plugins the webview may
  call. Only the core defaults.
- `src-tauri/icons/`: made from `static/favicon.svg` with `pnpm tauri icon static/favicon.svg`.
