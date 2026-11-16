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
