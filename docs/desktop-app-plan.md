# Plan: the sample-shepherd desktop app

A desktop app over the `sample-shepherd` CLI: browse and audition the library, run organize
and export, see what's on the device, review a sync plan visually, and watch a sync run.
Plan only, 2026-11-07. Nothing here is built yet, nothing touched a device, and no system
dependencies were installed.

## Summary

- **Shell: Tauri 2.** Small installers, native webview, a Rust core that stays thin.
- **UI: Svelte 5 (runes) with SvelteKit in SPA mode** (`adapter-static`, `ssr = false`, the
  setup Tauri documents). Less code than React for the same screens, and since the code is
  AI-written, React's bigger hiring pool matters less than reading less code in review.
- **Styling: Tailwind v4 with our own design tokens, and Bits UI for behavior only.** Bits UI
  gives accessible, unstyled dialogs, menus, comboboxes, sliders and so on; every pixel of
  look is ours. No component kit with a look of its own (no shadcn defaults, no Skeleton,
  no Flowbite).
- **TanStack: Virtual yes, Query yes, Table not at first.** TanStack Virtual renders 30,000
  rows smoothly. TanStack Query caches sidecar results and refetches after a command
  changes something (`svelte-query` 6 is runes-native). TanStack Table has a Svelte 5
  adapter too, but our sorting and filtering is a few `$derived` lines, so add Table only
  if column features grow (resizing, grouping, pinning).
- **Visuals: canvas for anything with many marks** (waveforms, the 30k-sample map, the
  +Drive map), **SVG with d3 modules for the rest** (`d3-hierarchy`, `d3-scale`,
  `d3-shape`, `d3-sankey`). d3 computes layouts; Svelte renders. (`d3-sankey` hasn't
  had a release since 2019; it works, and it's small enough to vendor if it breaks.) No charting library with
  its own look.
- **The Python CLI stays the brain.** It ships inside the app as a PyInstaller sidecar, and
  the app runs it one command at a time with a new `--json` event stream. Every safety rule
  (dry runs, `--yes`, project-usage guards, the device lock) stays in Python, where it's
  tested. The app can't skip a guard because it never reimplements one.
- **Licensing:** Fourier (Apache-2.0, our patched build) may ship with the app, with its
  LICENSE and NOTICE. Elektroid (GPLv3) never ships: the app finds a user-installed
  `elektroid-cli` and explains how to get one. See
  [research-fourier-elektroid.md](research-fourier-elektroid.md).

## Why this stack

| Choice | Over | Because |
|---|---|---|
| Tauri 2 | Electron | ~10 MB shell instead of ~150 MB; sidecars and scoped permissions are built in. Webview differences (WebKit on macOS and Linux, WebView2 on Windows) are the cost, so we test on all three |
| Svelte 5 | React | Fewer lines per screen, reactivity without hooks rules, scoped CSS. Jules's preference for less code wins |
| Svelte 5 | SolidJS | Solid is just as lean (its fine-grained signals are what Svelte 5's runes were modeled on) and Jules likes its look. But its ecosystem is smaller: no headless kit as complete as Bits UI, thinner TanStack adapters, fewer Tauri examples. Svelte gets the same small code with more off-the-shelf pieces |
| SvelteKit SPA | plain Vite + Svelte | File-based routes for ~8 screens, and it's Tauri's documented path. No server rendering |
| Tailwind v4 + tokens | CSS-in-JS, a UI kit | Tokens in one `@theme` block make the identity enforceable. Utilities keep components short |
| Bits UI | Melt UI, writing our own | Headless, Svelte 5 native, handles focus and keyboard and ARIA for us |
| TanStack Virtual / Query | hand-rolled | Both have Svelte adapters, and both solve real problems here (row count, cache invalidation) |
| canvas + d3 modules | Chart.js, ECharts, LayerCake | We want bespoke visuals. d3 gives math, not looks |

## Architecture

```
┌──────────────────────── Tauri app ───────────────────────────┐
│ Svelte UI (webview)                                          │
│   routes/ · components/ · viz/ · stores (runes)              │
│   TanStack Query ── invoke() / Channel ──┐                   │
│                                          ▼                   │
│ Rust core (src-tauri)                                        │
│   run_cli(cmd, args) → spawns sidecar, streams JSON events   │
│   cancel(run_id)     → "stop" line on stdin, kill on timeout │
│   peaks(path)        → waveform peaks, cached                │
│   audition(path)     → native playback (symphonia + rodio)   │
│   tools()            → finds elektroid-cli, fourier, sidecar │
└──────────┬──────────────────────────────┬────────────────────┘
           ▼                              ▼
  sample-shepherd sidecar          user-installed tools
  (PyInstaller onedir, resources)  elektroid-cli (GPLv3, never bundled)
           │                       fourier (bundled patched build, or the user's)
           └──── subprocess ───────────────┘
```

### What lives where

- **Python (sidecar):** all domain logic, as today: config, organize/export wrappers,
  device commands through `elektroid-cli`, project parsing, `plan`, `sync`, the locks and
  guards. The GUI adds output modes, never alternate logic.
- **Rust:** process plumbing and the few things that need speed or the OS: spawning and
  cancelling the sidecar (with `tokio::process`, not the shell plugin), streaming its
  events to the UI, decoding audio with `symphonia` for waveform peaks and for audition
  (played natively through `rodio`), finding tools on disk, and file dialogs.
  Kept small enough that a Python-only maintainer can follow it.
- **Svelte:** screens, visuals, and the audition controls. It never builds a command
  line from free text: it calls named Rust commands with typed arguments.

Audition is native rather than in the webview because webviews disagree on formats:
WebView2 can't play AIFF (common in sample packs) and WebKitGTK needs GStreamer plugins.
Rust already decodes for peaks, and native playback is also lower-latency for `J`/`K`
browsing.

### Sidecar protocol

Add a global `--json` flag to the CLI. With it, a command writes one JSON object per line
to stdout and nothing else (human text goes to stderr):

```json
{"v":1,"type":"start","cmd":"sync","dry_run":true}
{"v":1,"type":"progress","done":120,"total":846,"bytes":9830400,"eta_s":5410}
{"v":1,"type":"row","kind":"plan","action":"upload","device_path":"/kicks/…","size":81920}
{"v":1,"type":"warn","msg":"3 names over 32 characters"}
{"v":1,"type":"result","ok":true,"summary":{"upload":846,"delete":12,"keep_used":71}}
{"v":1,"type":"error","code":"device_busy","msg":"…"}
```

- `v` is the schema version, an integer bumped on any breaking change. The app refuses any
  `v` it doesn't know.
- **Stdout is only events.** In `--json` mode the CLI, at startup, keeps the real stdout
  as a private file descriptor for events and points fd 1 at stderr. So a stray `print`,
  tqdm, or a child process (Fourier, PyTorch) can't corrupt the stream. One pytest makes a
  child print to stdout and checks the stream still parses.
- Exit codes stay as they are (0, 2 user error, 3 device error, 130 stopped).
- A pytest per command checks its event shapes against a JSON Schema in
  `src/sample_shepherd/events.schema.json`, and the UI generates TypeScript types from the
  same file, so the two can't drift.
- **One process per command, at first.** It matches the CLI, keeps the per-device lock
  simple, and a crash can't wedge the app. The sidecar is a PyInstaller `onedir` build
  (no unpacking on each launch, unlike `onefile`), so it starts in well under a second. If library browsing makes startup cost add up, add `sample-shepherd serve
  --stdio` (JSON-RPC over stdin and stdout) for read-only queries only; writes and device
  commands stay one-shot.
- **Cancel is cooperative.** The app writes `{"type":"stop"}` to the sidecar's stdin.
  `sync` checks for it between files, finishes the current transfer (so `elektroid-cli`
  is never killed mid-file, which could leave a partial file on the device), logs it, and
  exits through the existing "stopped, rerun to resume" path. This works the same on every
  OS, unlike signals: Windows has no SIGINT for a GUI app's child, and a signal to the
  Python process alone would make `subprocess.run` kill `elektroid-cli` mid-transfer. A
  hard kill is only a fallback after a timeout, with a warning. pytest covers "stop
  between files" with the fake device.

### New CLI pieces the app needs

1. `--json` on every command (above).
2. `library index --json`: scan a curated master (read-only) and write a SQLite cache in
   the app's data folder: path, folder, category, duration, sample rate, channels, size,
   content hash, and the rating from Fourier's review data when there is one (read-only,
   the same ratings `fourier review` sets; the column is simply empty without them). Incremental by mtime and size. The browser queries this.
3. `tools --json`: the versions and paths of `elektroid-cli` and `fourier`, and what each
   enables. The onboarding screen is this command, drawn.
4. `plan --json` row stream and `plan edit` (exclude or include rows by id), so a reviewed
   plan stays a CSV the CLI checks again at sync time.

All four are useful from the terminal too, and each gets tests without a device.

### Safety in the app

- **The plan is the dry run.** The Sync screen only accepts a plan the Plan screen
  produced and showed. Starting a sync with deletes asks for the number of deletes typed
  back, then passes `--yes`. The CLI still checks every delete again.
- **Sources are read-only because Python says so.** The sidecar (and Fourier under it)
  runs with the user's full permissions; Tauri's scopes only limit the webview. So the
  guarantee is the CLI's: it never writes to the source library or the master, and that
  stays tested in pytest. The **Ableton User Library is never written, by anything**, and
  is left out of the webview's fs and asset scope entirely (audition goes through Rust,
  which only reads). Writes go to `work_dir`, export folders the user picks, and app data.
- **No shell permissions in the webview.** Svelte calls named Rust commands with typed
  arguments; Rust spawns the sidecar itself; Python runs `elektroid-cli`. So the Tauri
  shell plugin isn't used and `elektroid-cli` is in no Tauri scope: `tools()` only finds
  it and passes its path to the CLI through config.
- **Device busy** shows as a banner from the lock file, and device buttons go disabled.
  The app can't see Elektron Transfer either, so it says so before any device command.
- Nothing the app does depends on the device for its tests: Rust and UI tests run the
  sidecar against fixtures and a fake `elektroid-cli` script, as pytest already does.

## Design direction

The brief: bespoke, not a generic AI-app or Bootstrap look. The direction is
**"field manual"**: the app should feel like a well-made instrument and its printed
manual, not like a SaaS dashboard.

- **Surface:** warm paper (`#F3F0E8`-ish) and ink (`#16150F`) in light mode; a deep
  warm-black console (`#121110`) with the same ink tones inverted in dark mode. Flat. No
  drop shadows, no gradients, no glass, no rounded-2xl cards. Panels are separated by 1px
  hairlines and a visible grid.
- **One signal color:** a hot orange-red (`#FF4A1C`-ish) used only for "this will change
  something" (record, upload, delete, the active transfer). Everything else is ink at
  different weights. Deletes use the signal color plus a hatched pattern, so they read
  without color too.
- **Category palette:** one fixed, desaturated hue per sample category (kick, snare, hat,
  perc, bass, tonal, fx, foley, loop, vocal). Used identically in the table, the waveform
  tint, the library map, the +Drive map and the plan. Learn it once, read it everywhere.
  Checked for color-blind separation and contrast in both themes.
- **Type:** *Departure Mono* (OFL) for labels, numbers, paths and anything echoing a
  device screen; *Instrument Sans* (OFL) for prose and controls. Tabular numerals
  everywhere. Small caps for section labels. Both fonts ship in the app.
- **Density:** pro-audio dense. 28px rows, keyboard first (`J`/`K` to move, `Space` to
  audition, `/` to filter, `Enter` to open), every action reachable from a command
  palette (`⌘K`).
- **Motion:** only where it carries meaning: the playhead, transfer progress, a plan row
  sliding from "upload" to "done". 120–180 ms, no bouncing. Respects reduced motion.
- **Texture with restraint:** a faint dot grid behind empty states, registration marks at
  panel corners, hand-set folder numbers (`01 KICKS`) mirroring the device's folder
  layout.

**Bits UI doesn't limit the look.** It ships no styles: each part (`Dialog.Content`,
`Select.Item`, …) renders a plain element we give classes to, exposes its state as data
attributes (`data-state="open"`, `data-highlighted`) to style against, and a `child`
snippet lets us render our own element in its place. What it saves us is the hard,
invisible part: focus trapping, keyboard navigation, typeahead, positioning and ARIA. That
is a lot less code than writing those from scratch, and none of it shows. Where Bits UI has
no component (the waveform, the maps, the transport), we write our own anyway.

Before building screens, make a one-page style sheet in the app (`/dev/style` route):
tokens, type scale, the category palette, buttons, inputs, a table, a waveform. Jules
reviews that one page; every later screen reuses it.

## Screens

1. **Setup.** Finds the tools (`tools --json`): the bundled sidecar, Fourier (bundled or
   the user's), `elektroid-cli` (user-installed, with per-OS steps from the README), and
   writes the config. Shows Fourier's CLAP research-use notice where it asks for the
   model.
2. **Library.** Folder tree (the four-level layout: section, category, subfolder) on the
   left, a virtual table in the middle (name, category, duration, channels, rating, size),
   and an inspector on the right with the waveform, spectrum thumbnail and metadata. Space
   auditions; arrow keys audition as you move. Filter by text, category, duration, mono or
   stereo, rating.
3. **Organize.** Runs `organize build` (dry run first), then shows what moved: before and
   after counts per folder, renamed files, dropped duplicates. Links each change to the
   Library.
4. **Export.** Pick a profile, render (dry run first), then `export check` results as a
   list of issues you can click through (names over 32 characters, over-full folders,
   formats).
5. **Device.** The connected device, its filesystems, the +Drive map (below), project
   slots with their last backup, and a Backup button. Read-only unless you press Backup.
6. **Plan.** The sync plan drawn as a flow (below) above the row list. Rows can be
   excluded; protected and project-used rows explain why they're kept. Writes the plan CSV.
7. **Sync.** Live progress from the event stream: bytes, files, ETA at the link's real
   rate (about 77 KB/s on the Digitakt II), current file's waveform as the progress bar,
   a log you can filter, Stop (resumable) and Resume.
8. **Settings.** Paths, work folder, theme, keyboard shortcuts.

## Visualizations

Ordered by how much each helps; the first four are in scope for v1.

1. **Waveform strips** (canvas). Peaks computed in Rust once per file and cached, drawn
   in the category's hue. Mini strips in table rows, a full one in the inspector with a
   playhead and loop region. Stereo files draw two lanes, so mono versus stereo is visible
   at a glance (it matters: only the Digitakt II keeps stereo).
2. **+Drive map** (canvas). The device's storage as a grid of cells, one per sample,
   sized by bytes and colored by category, grouped by folder. Samples a project uses get a
   solid outline; ones the plan would delete get the hatch. Free space is empty paper. You
   see at once what fills the drive and what's safe to clear.
3. **Plan flow** (SVG, `d3-sankey`). Two flows, stacked: the export flowing into the
   device (upload, skip because it's already there), and what's on the device flowing out
   to its fate (keep because a project uses it, keep because it's protected, keep, delete).
   Band widths are bytes, so the cost of a sync in transfer time is visible before you start.
   Clicking a band filters the row list.
4. **Library terrain** (SVG, `d3-hierarchy` icicle). Section → category → folder →
   files, width by count or bytes. Doubles as navigation for the Library screen, and makes
   lopsided folders (the ones `FOLDER_ADAPTIVE` splits) obvious.
5. **Project constellation** (canvas, force layout). Projects as large nodes, the samples
   they use as small ones, shared samples pulled between them. Shows which samples many
   projects depend on before you reorganize.
6. **Sound map** (canvas, later). A 2D layout of every sample by timbre (from Fourier's
   CLAP embeddings if it exposes them, or cheap features: spectral centroid, attack,
   length), colored by category. Hover auditions. Good for finding near-duplicates and
   gaps.
7. **Transfer timeline** (SVG). Each sync session as a bar per file over time; shows
   stalls and how long the device took per MB. Built from the existing log CSVs.

### Later: WebGL

v1 is d3 for layout and math, drawn with SVG or canvas 2D. Each visual sits behind a small
component boundary (data in, events out), so any one of them can move to WebGL later
without touching the screens around it. Candidates, for when canvas runs out or for fun:

- **Sound map in 3D** (`regl` or `three.js`): all 30,000 samples as points in a timbre
  space you fly through; points pulse as they're auditioned, nearest neighbours light up.
  WebGL handles that point count at 60 fps where canvas 2D struggles.
- **Spectrogram waterfall:** the inspector's waveform as a scrolling, shaded spectrogram
  during playback, FFT frames computed in Rust alongside playback and drawn as a texture.
- **+Drive map as a shader:** the storage grid as one instanced draw, so hover, zoom and the
  sync animation (cells filling as uploads land) stay smooth on a full drive.
- **Sync as a particle flow:** the plan's Sankey bands as streams of particles moving at the
  link's real byte rate during a sync.

Rules for these: same tokens and category palette as everything else, a 2D fallback when
WebGL is unavailable or reduced motion is on, and nothing essential exists only in the
WebGL view.

## Repository layout

```
app/                     the desktop app (new)
  package.json           pnpm, Vite, SvelteKit, Tailwind, Bits UI, TanStack, d3
  src/                   routes/, lib/components, lib/viz, lib/sidecar (typed client)
  src-tauri/             Rust core, tauri.conf.json, capabilities/
  sidecar/               PyInstaller spec and build script for the CLI
src/sample_shepherd/     unchanged home of the logic; gains --json, library index, tools
scripts/                 untouched: ~/sample-work/scripts symlinks into it
```

## Packaging per OS

The sidecar is built by PyInstaller on each OS and architecture (it can't cross-compile)
as a `onedir` folder: an executable plus `_internal/`. Tauri's `bundle.externalBin` takes
only a single executable, so the folder ships under `bundle.resources`, and Rust spawns
it by its resolved path. Fourier, if bundled, is a second `onedir` build the same way.

**Licenses in the bundle.** Fourier ships with its LICENSE, NOTICE and
`THIRD_PARTY_NOTICES.md`, plus our patch series (`config/patches/`) as the record of what
we changed. A PyInstaller bundle carries every transitive dependency, so the build
collects their licenses (`pip-licenses`, and `cargo about` for Rust) into a notices file
in the app, and fails on anything copyleft for a human to decide. This applies to our own
sidecar too, and runs before any release.

| OS | Installer | Notes |
|---|---|---|
| macOS (arm64, x86_64) | `.dmg` / `.app` | Signing and notarization need an Apple Developer ID (Jules's account and cost). Every executable, `.so` and `.dylib` inside both `onedir` sidecars is signed too, with the hardened runtime. Without signing, users must right-click → Open. `elektroid-cli` is built from source (README steps), so Setup links to them |
| Windows (x86_64) | NSIS `.exe` (or `.msi`) | WebView2 bootstrapper included. Elektroid has no official Windows build, so sync is unavailable there unless the user provides `elektroid-cli`; organize, export and the library work |
| Linux (x86_64) | `.AppImage`, `.deb` | `apt install elektroid` provides `elektroid-cli`. WebKitGTK 4.1 is a runtime dependency of the `.deb` |

- **CI:** a GitHub Actions matrix (macOS arm64 and x86_64, Windows, Ubuntu) builds the
  sidecar, then `tauri build`, and uploads artifacts to the run. Publishing a release (and
  turning on `tauri-plugin-updater`) waits for Jules's OK, since it publishes.
- **Size:** the shell is about 10 MB and the CLI sidecar about 20 MB. Fourier with CLAP
  pulls in PyTorch (hundreds of MB to a few GB), so the plan is: ship Fourier without the
  CLAP extra, and download the model and torch into app data on first use, with consent
  and the research-use notice. Open question 2 below.

## Testing

The app is AI-written, so tests are how we know it works. But each risk gets tested
once, at the cheapest layer that can catch it, and nothing is tested twice in different
clothes. Three layers, all in CI, none needing a device:

| Layer | Owns this risk | Doesn't re-test |
|---|---|---|
| pytest | Logic and safety: plan, sync, guards, parsing, `--json` output | UI, process plumbing |
| Playwright | The UI does the right thing with what the CLI sends; how it looks | Logic the CLI decides |
| A few small unit tests (Rust, Vitest) | Code with real branching outside Python: cancel, event parsing, viz layout math | Anything above |

### pytest: logic, safety and the full loop

What exists today, extended:

- **Guards, once, thoroughly.** Property-based tests (Hypothesis) for `plan` and `sync`:
  for any listing, usage list and export, no delete names a used path, a used hash or a
  protected path, and none appears without a usage list. This is the most important test
  in the project, so it lives in exactly one place.
- **The closed loop, with a fake device.** The stateful fake `elektroid-cli` that
  already exists in `tests/fake/` (a pretend +Drive in a temp folder, printing what the
  real tool prints), extended as the app needs new commands or failure modes, runs a handful of scenarios end to end: backup → used → plan → sync leaves the device
  matching the plan; a sync killed halfway resumes without re-uploading; an unsupported
  device says "not available" instead of an empty used list. Only scenarios the unit
  tests can't reach go here.
- **The contract.** Each `--json` command is checked against `events.schema.json`, and the
  same test run saves its event streams as the UI's fixtures. The UI's TypeScript types are
  generated from the schema. So Python and the UI share one source of truth, without a
  separate contract-test layer.

### Playwright: flows and looks

- **The built frontend in WebKit** (the engine of the macOS and Linux webviews; WebView2 on
  Windows is Chromium and rarely the one that breaks), with Tauri's IPC mocked to replay
  the fixture streams from pytest.
- **A few critical flows,** not every screen: setup with a tool missing, build and edit a
  plan, a sync with a device error and a resume, the typed delete confirmation. Each
  checks what the user sees, trusting pytest for whether the plan itself is right.
- **Screenshots** of the style sheet page and each screen with fixture data, light and
  dark, in a pinned Playwright Docker image so pixels are stable. A diff fails the PR and
  shows the before, after and diff images; updating a baseline is a deliberate commit.
  These double as what the reviewer looks at to judge the design. One `axe` accessibility
  check per screen rides along in the same tests.

### Small unit tests where the logic is

Rust: event-line parsing and cancel (the stop line, then the timeout). Vitest: viz layout
functions (the +Drive packing, the Sankey bands) and the sidecar client's handling of
errors. No tests for components that only render props.

### Left out on purpose, until a real bug says otherwise

- A second browser engine in Playwright.
- Driving the packaged app through `tauri-driver`. The IPC layer is thin; the release
  smoke checklist (install, open, run a dry-run plan) covers it, by hand, per OS.
- Re-running the closed loop from Rust: the Rust code that spawns the sidecar is small
  enough for its unit tests.
- Coverage targets. Coverage follows risk, not a number.

### On a real device

Only after Jules says the live sync is finished, following the device-session checklist,
and never in CI. A real run's event stream and listings (names only, no audio) can become
new fixtures.

## Milestones

1. **Foundations.** `--json` events and their schema; `tools`; the `app/` scaffold; the
   style sheet page; the sidecar build on one OS (macOS arm64). Review the look here.
2. **Library.** `library index`, the browser, waveforms, audition, the terrain.
3. **Organize and export.** Wrapped runs with dry-run-first, check results.
4. **Device and plan.** Device screen with the +Drive map, backups, Plan with the flow,
   `plan edit`. Still nothing written to a device: plan is read-only on the device.
5. **Sync.** The live run screen. First real run only with Jules, after the current sync
   finishes.
6. **Packaging.** CI matrix, signing, installers. Then the later visualizations.

## Open questions for Jules

1. **Design direction.** "Field manual" (paper and ink, one signal color) as described, or
   a darker "console" direction first? The style sheet page in milestone 1 is where to
   decide; changing tokens later is cheap.
2. **Fourier in the app.** Bundle it without CLAP and download the model on first use
   (recommended), bundle everything (large installer), or require the user's own install?
3. **Signing.** Is an Apple Developer ID available for notarized macOS builds? Without it,
   builds still work for personal use.
4. **Windows.** Worth a Windows build in v1, given sync needs an `elektroid-cli` that
   Elektroid doesn't ship for Windows?
5. **License for sample-shepherd itself.** Still Jules's call; it doesn't block the app,
   but it does block publishing any release.
