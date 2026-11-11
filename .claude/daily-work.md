budget_minutes: 60

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
