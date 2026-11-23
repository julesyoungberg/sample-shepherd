budget_minutes: 45

# Daily work log

One entry per run of the "Daily Project Work: Sample Shepherd" task (weekday and weekend
triggers share this file). Newest last.

## 2026-11-08 (Sunday, weekend run)

- Minutes used: about 30 of 60. Subagents: 0.
- Shipped: draft PR "Add --json event stream and `tools` command" (desktop app milestone 1,
  first two items): `src/sample_shepherd/events.py`, `events.schema.json`, global `--json`,
  `tools`, docs, tests.
- State found: tests green on main (after `uv pip install -e '.[dev]'`; plain `uv run pytest`
  fails to import the package in a fresh checkout). No open issues. Open PRs #10 and #11 are
  in the agent review loop, left alone.
- Next: `row`/`progress`/`warn` events for the other commands (`plan` rows first, then
  `sync` progress and cooperative stop on stdin), then `library index`. App scaffold and the
  /dev/style page after that.
- Open questions for Jules (from docs/desktop-app-plan.md, still open): design direction
  (field manual vs console), bundling Fourier, Apple Developer ID, Windows in v1, license.
- Budget: first run, no change.

## 2026-11-09 (Monday, weekday run)

- Minutes used: about 25 of 60 (active work; review wait not counted). Subagents: 0.
- Shipped: PR "Stream plan rows and totals as --json events" (desktop app plan, CLI piece 4,
  first half): `plan --json` row events, `plan.totals()`, schema, docs, one test.
- State found: tests green on main, no open PRs or issues. PR #12 merged.
- Next: `sync --json` progress events and cooperative stop on stdin (the plan's "Cancel is
  cooperative"), then `plan edit` (needs row ids), then `library index`. App scaffold and
  the /dev/style page after that.
- Open questions for Jules (docs/desktop-app-plan.md, still open): design direction, bundling
  Fourier, Apple Developer ID, Windows in v1, license.
- Budget: only two runs logged, no change.

## 2026-11-10 (Tuesday, weekday run)

- Minutes used: about 30 of 60 (active work; review wait not counted). Subagents: 0.
- Shipped: PR "Report sync progress and stop a sync from the app" (desktop app plan, CLI
  piece 1 and "Cancel is cooperative"): `progress` events, a `{"type": "stop"}` line on
  stdin stops `sync` between files, sync `result` summary, docs, two tests.
- State found: tests green on main, no issues. PR #13 (plan rows, the 2026-11-09 run's) was
  approved and left to its author; it merged during this run, and only this log needed a
  hand merge.
- Next: `plan edit` (needs row ids), then `library index`. App scaffold and the /dev/style
  page after that (the scaffold adds Node and Rust tooling, so check with Jules first).
- Open questions for Jules (docs/desktop-app-plan.md, still open): design direction, bundling
  Fourier, Apple Developer ID, Windows in v1, license.
- Budget: 30, 25 and 30 minutes of 60; not all under half, so no change.

## 2026-11-11 (Wednesday, weekday run)

- Minutes used: about 25 of 60 (active work; review wait not counted). Subagents: 0.
- Shipped: PR "Add plan-edit: turn plan rows off or back on by id" (desktop app plan, CLI
  piece 4, second half): `id` on plan row events, `plan-edit --exclude/--include`,
  `excluded-upload`/`excluded-delete` actions, schema, docs, three tests. Named `plan-edit`
  rather than `plan edit` because `plan` already takes flags and can't also have
  subcommands; the app plan doc says `plan-edit` now.
- State found: tests green on main, no open PRs or issues.
- Next: `library index` (SQLite cache of the master, read-only). Then the app scaffold and
  /dev/style page, which add Node and Rust tooling, so check with Jules first.
- Open questions for Jules (docs/desktop-app-plan.md, still open): design direction, bundling
  Fourier, Apple Developer ID, Windows in v1, license.
- Budget: 30, 25 and 25 minutes of 60; not all under half, so no change.

## 2026-11-12 (Thursday, weekday run)

- Minutes used: about 25 of 60 (active work; review wait not counted). Subagents: 0.
- Shipped: PR #16 "Add library index: a read-only SQLite index of a library"
  (https://github.com/julesyoungberg/sample-shepherd/pull/16; desktop app plan, CLI piece 2):
  `library index LIBRARY --db`, incremental by size and mtime, category from folder names,
  WAV duration/rate/channels, SHA-256, guards against an index inside the library or of
  another library, docs, three tests. Separate refactor commit: `wav_info` in util.py.
- State found: tests green on main, no open PRs or issues.
- Next: fill the index's `rating` column from Fourier's ratings.json (needs the master's
  manifest.json `out` format confirmed against a real master). Then the app scaffold and
  /dev/style page, which add Node and Rust tooling, so check with Jules first.
- Open questions for Jules: OK to add Node and Rust tooling for the app scaffold? Plus the
  ones in docs/desktop-app-plan.md: design direction, bundling Fourier, Apple Developer ID,
  Windows in v1, license.
- Budget: 30, 25 and 25 minutes of 60; 30 isn't under half, so no change.

## 2026-11-13 (Friday, weekday run)

- Minutes used: about 25 of 60 (active work; review wait not counted). Subagents: 0.
- Shipped: PR "Fill the library index's rating from Fourier's ratings.json" (desktop app
  plan, CLI piece 2, the rating column): `library index --ratings`, `load_ratings`, docs, one
  new test and the CLI test extended. The open question from the last run (how a source-path
  rating maps to a master file) answered itself: each rating in ratings.json records `out`,
  its path in the master, as config/ratings-snapshot.json shows.
- State found: tests green on main, no open PRs or issues. `graphify` isn't installed in the
  cloud container, so the graph wasn't rebuilt.
- Next: the app scaffold and /dev/style page, which add Node and Rust tooling, so they wait
  for Jules's OK. Nothing CLI-side is left in milestone 1 of docs/desktop-app-plan.md.
- Open questions for Jules: OK to add Node and Rust tooling for the app scaffold? Plus the
  ones in docs/desktop-app-plan.md: design direction, bundling Fourier, Apple Developer ID,
  Windows in v1, license.
- Budget: 25, 25 and 25 minutes of 60; 30 is half, and 25 is under it, so all three ran
  under half: lowered budget_minutes from 60 to 45.

## 2026-11-14 (Saturday, weekend run)

- Minutes used: about 20 of 45 (active work; review wait not counted). Subagents: 0.
- Shipped: PR #23 "Report library index progress as --json events"
  (https://github.com/julesyoungberg/sample-shepherd/pull/23; for the app's library screen,
  milestone 2): a `progress` event after each file `library index` reads, same shape as
  `sync`'s; schema descriptions, docs, one test.
- State found: tests green on main, no open PRs or issues. Many old `claude/project-thread-*`
  branches on the remote from merged PRs; left alone (deleting them is Jules's call).
- Next: the app scaffold and /dev/style page, which add Node and Rust tooling, so they wait
  for Jules's OK. Small CLI follow-up if needed: stop a `library index` run from the app.
- Open questions for Jules: OK to add Node and Rust tooling for the app scaffold? Plus the
  ones in docs/desktop-app-plan.md: design direction, bundling Fourier, Apple Developer ID,
  Windows in v1, license.
- Budget: 25, 25 and 20 minutes; 25 isn't under half of 45, so no change.

## 2026-11-15 (Sunday, weekend run)

- Minutes used: about 10 of 45 (active work). Subagents: 0.
- Shipped: nothing new. Tests green on main (112 passed), docs/cli/reference.md current.
- State found: PR #23 (library index progress events, the 2026-11-14 run's) was approved
  but not merged; its thread merged it after a nudge. No open issues.
- Considered and skipped: a cooperative stop for `library index`. It only reads the library
  and writes its own SQLite cache, so the app can simply kill it; `sync` is the only command
  that needs a stop line.
- Next: the app scaffold and /dev/style page, still waiting for Jules's OK on Node and Rust
  tooling (asked again as a decision card). Nothing CLI-side is left in milestone 1.
- Open questions for Jules: the Node and Rust OK, plus those in docs/desktop-app-plan.md:
  design direction, bundling Fourier, Apple Developer ID, Windows in v1, license.
- Budget: 25, 20 and 10 minutes of 45; 25 isn't under half, so no change.

## 2026-11-16 (Monday, weekday run)

- Minutes used: about 30 of 45 (active work; review wait not counted). Subagents: 0.
- Shipped: PR "Add the app frontend scaffold and the /dev/style page" (milestone 1 of
  docs/desktop-app-plan.md): `app/` with SvelteKit SPA and Tailwind v4 tokens, the style
  sheet at `/dev/style` (surfaces, type, category palette, buttons, inputs, table, canvas
  waveform, Paper/Console toggle), Playwright tests, app/README.md, doc updates.
- Found while testing: Tailwind v4 drops theme variables no utility uses, so the category
  colors rendered transparent; fixed with `@theme static`. Two first-pick colors (snare, hat)
  were under 3:1 on paper; the palette now shares one lightness at about 4:1 on both themes.
- Skipped: the Tauri shell (`src-tauri/`). Building it needs WebKitGTK dev packages, a
  system dependency the cloud container lacks, so it can't be checked here. Bits UI,
  TanStack and d3 wait until a screen needs them. Playwright runs Chromium, not WebKit as
  the plan says, because only Chromium is installed in cloud sessions.
- Next: the Tauri shell, checked on Jules's Mac or with WebKitGTK installed (needs Jules's
  OK); color-blind check of the category palette; screenshot baselines.
- Open questions for Jules: pick the look on /dev/style (Paper or Console first); OK to
  install WebKitGTK in the cloud environment, or build the shell on the Mac? Plus those in
  docs/desktop-app-plan.md.
- Budget: 20, 10 and 30 minutes of 45; 30 isn't under half, so no change.

## 2026-11-17 (Tuesday, weekday run)

- Minutes used: about 25 of 45 (active work; review wait not counted). Subagents: 0.
- Shipped: PR "Add library ls: list the indexed samples, as --json rows for the app"
  (milestone 2 of docs/desktop-app-plan.md). The plan said the browser "queries" the index
  but not how; `library ls --json` streams one `row` event (kind `sample`) per sample, in
  line with "one process per command". Schema, docs and one test.
- State found: tests green on main (pytest and `pnpm check`), no open PRs or issues.
- Next: the Library screen in `app/` (virtual table, folder tree, filters) fed by these
  rows from a fixture until the Tauri shell exists. The Tauri shell still waits on
  WebKitGTK in the cloud env or a build on Jules's Mac.
- Open questions for Jules: Paper or Console look on /dev/style; WebKitGTK in the cloud
  environment or build the shell on the Mac. Plus those in docs/desktop-app-plan.md.
- Budget: 10, 30 and 25 minutes of 45; not all under half or at the cap, so no change.

## 2026-11-18 (Wednesday, weekday run)

- Minutes used: about 25 of 45 (active work; review wait not counted). Subagents: 0.
- Shipped: PR "Add the Library screen: folder tree, sample table and filters" (milestone 2
  of docs/desktop-app-plan.md). `/library` in `app/` reads a recorded `library ls --json`
  run; filters by text, folder, category, channels and rating. Fourier's 19 categories map
  onto the 10 palette colors in `app/src/lib/library.js`.
- Skipped: TanStack Virtual (the table renders at most 500 rows, marked as a shortcut);
  the inspector, waveforms and audition, which need audio from the Tauri shell.
- State found: tests green on main, no open PRs or issues.
- Next: the library terrain (d3-hierarchy icicle) from the same rows, or the Tauri shell
  once WebKitGTK or the Mac is available.
- Open questions for Jules: Paper or Console look (screenshots of both in project files,
  app-style/); WebKitGTK in the cloud environment or build the shell on the Mac.
- Budget: 30, 25 and 25 minutes of 45; not all under half or at the cap, so no change.

## 2026-11-19 (Thursday, weekday run)

- Minutes used: about 25 of 45 (active work; review wait not counted). Subagents: 0.
- Shipped: PR #28 "Refuse a --db that isn't a library index instead of a traceback"
  (https://github.com/julesyoungberg/sample-shepherd/pull/28), the known gap from 11-17.
  PR #29 "Add the library terrain: folders as bands sized by sample count"
  (https://github.com/julesyoungberg/sample-shepherd/pull/29), milestone 2 visual 4.
  Screenshots in project files, app-style/terrain-*.png.
- Choice: the terrain is positioned buttons laid out in `library.js`, not SVG with
  `d3-hierarchy`: no new dependency, and keyboard reachable. The plan says so now.
- State found: tests green on main, no open PRs or issues.
- Next: what's left of milestone 2 (waveforms, audition, inspector) needs audio from the
  Tauri shell, which still waits on WebKitGTK in the cloud env or a build on Jules's Mac.
  Without it: TanStack Virtual for the table, or start milestone 3 screens from fixtures.
- Open questions for Jules: Paper or Console look; WebKitGTK in the cloud environment or
  build the shell on the Mac.
- Budget: 25, 25 and 25 minutes of 45; not all under half or at the cap, so no change.

## 2026-11-20 (Friday, weekday run)

- Minutes used: about 25 of 45 (active work; review wait not counted). Subagents: 0.
- Shipped: PR "Add export check --json issue rows and the Export check screen" (milestone 3
  of docs/desktop-app-plan.md). `export check --json` sends every issue as a `row` (kind
  `issue`), not only the first `--show`; `/export` in `app/` lists them from a recorded run.
  Screenshots in project files, app-style/export-*.png.
- Skipped: clicking an issue through to the Library (the index holds master paths, not
  render paths); the render step with its dry run, which needs Fourier from the shell.
- State found: tests green on main, no open PRs; issue #30 still open (no user path hits it).
- Next: the Organize screen from a recorded `organize build` run (needs `--json` rows for
  what moved), or the Tauri shell once WebKitGTK or the Mac is available.
- Open questions for Jules: Paper or Console look; WebKitGTK in the cloud environment or
  build the shell on the Mac.
- Budget: 25, 25 and 25 minutes of 45; not all under half or at the cap, so no change.

## 2026-11-22 (Sunday, weekend run)

- Minutes used: about 25 of 45 (active work; review wait not counted). Subagents: 0.
- Shipped: PR "Keep library.index() from adding tables to a db that isn't an index"
  (fixes issue #30). `index()` checks an existing db before creating its tables.
- Tried and stopped: wiring the Library screen to the real CLI through the Tauri shell.
  It needs `@tauri-apps/api` (Tauri's own JS package for `invoke()`), a new dependency,
  so it waits on Jules.
- State found: tests green on main, no open PRs; #30 was the only open issue.
- Next: once Jules OKs `@tauri-apps/api`, a `library_ls` Rust command that runs
  `sample-shepherd --json library ls` from PATH and feeds `/library`. After that the
  PyInstaller sidecar build, which is also a new dependency.
- Open questions for Jules: OK to add `@tauri-apps/api` (app) and PyInstaller (build only)?
- Budget: 25, 25 and 25 minutes of 45; not all under half or at the cap, so no change.

## 2026-11-23 (Monday, weekday run)

- Minutes used: about 25 of 45 (active work; review wait not counted). Subagents: 0.
- Shipped: PR "Add the Sync plan screen: totals, the plan flow and every row" (milestone 4
  of docs/desktop-app-plan.md). `/plan` in `app/` reads a recorded `plan-edit --json` run.
  The flow is positioned buttons laid out in `plan.ts` (no `d3-sankey`, so no new
  dependency); bands are bytes on one scale, and clicking one filters the rows.
  Screenshots in project files, app-style/plan-*.png.
- Skipped: excluding rows from the screen (needs the sidecar); the +Drive map and Device
  screen (no recorded listing fixture yet).
- State found: tests green on main, no open PRs or issues. Yesterday's question on
  `@tauri-apps/api` and PyInstaller is still unanswered.
- Next: the Device screen's +Drive map from a recorded `device listing` CSV, or the
  sidecar wiring once Jules OKs the two dependencies.
- Open questions for Jules: OK to add `@tauri-apps/api` (app) and PyInstaller (build only)?
- Budget: 25, 25 and 25 minutes of 45; not all under half or at the cap, so no change.
