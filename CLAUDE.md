# CLAUDE.md

Notes for Claude (and anyone else) working in this repo. The README is for users; this file
is the rules for changing the code. When the same correction comes up twice, propose adding
it here.

## Commands

- Set up: `uv venv && uv pip install -e '.[dev]'`
- Test: `.venv/bin/pytest` (or `uv run pytest`). Must pass with no device attached. There is
  no CI, so this run before every push is the check.
- After any change to a command or flag: `python -m sample_shepherd.cli_reference > docs/cli/reference.md`.
  The file is generated (never edit it by hand) and `tests/test_cli_reference.py` fails while it's stale.
- No linter or formatter is configured. Match the style of the file you're in.

## Never

These protect Jules's device, projects and libraries. Breaking one can lose real work.

- Never run the real `elektroid-cli` or talk to a connected Elektron device. A live device
  sync is running; hands-on device work waits until Jules says it's finished, then follows
  `docs/device-session-1-checklist.md`. Tests use the fake in `tests/fake/elektroid-cli`.
- Never write to `~/sample-work/out`, `~/sample-work/device`, the Ableton User Library, or the
  SanDisk Extreme SSD (it's the Time Machine disk). Source libraries are read-only input
  everywhere, in code and by hand.
- Never commit audio (`.gitignore` blocks wav/mp3/aif/flac). Generate it at test time with
  `make_wav` in `tests/conftest.py`.
- Never bundle, vendor or import Elektroid code: it's GPLv3, so it only runs as a separate
  program. Fourier has no Python API either; call the `fourier` CLI as a subprocess.
- Never move or rename anything in `scripts/`: they run by path and `~/sample-work` symlinks
  to them. `tests/test_legacy_scripts.py` checks they still compile.
- Never publish anything, or open issues or PRs on other repos (Fourier, Elektroid), without
  Jules's OK. PRs on this private repo are fine.

## Safety invariants in the code

Any new command must keep these; `tests/test_sync_guards.py` pins the existing ones.

- Every command that writes files or touches a device has `--dry-run`, which prints what it
  would do (with a time and size estimate for transfers) and changes nothing.
- Nothing deletes without `--yes`, and nothing deletes a sample a backed-up project uses
  (matched by path or content hash). With no project list, nothing is deletable.
- Uploads never overwrite. Deletes run last, only after every upload succeeded.
- Device access goes through `device_lock` in `util.py`.
- Paths come from config or flags, never hardcoded. Unknown config keys are errors, so a new
  setting goes in `config.py` and `docs/cli/configuration.md` together.

## Build what the task needs now

Build what's asked, in a shape that's cheap to change later. Minimize scope, never correctness.

- Solve the stated requirement. No speculative features, config options, flags or extension
  points nobody has asked for.
- Extensibility comes from simplicity: small functions, clear names, explicit data flow, and
  dependencies passed in (as `ElektronDevice` takes a `runner`), not from new base classes,
  plugin systems or frameworks built ahead of need.
- Abstract on the third repetition, not the first. Duplication is cheaper than the wrong
  abstraction.
- Reuse what exists and don't add a second way to do the same thing. If unsure which pattern
  is canonical, ask.
- No new dependency (runtime is just `pyyaml`) without saying why and asking Jules first.
  The same goes for system packages.
- Keep diffs focused: every changed line traces to the task. A small rename or refactor in
  code you're already touching is fine when it makes that code clearer; put it in its own
  commit and name it in the PR. Leave untouched files alone, and never reformat.
- Validation, error handling at boundaries (config, CSV input, device output) and tests still ship.
- For non-trivial work, state your assumptions and the simplest viable approach before
  coding, and ask when something is ambiguous instead of guessing.
- Define done as something verifiable (a test, a command and its output) and check it
  before you say it's done.
- If you spot something worth building later, note it in the PR description or as an issue
  on this repo rather than building it now.

## Where code goes

- A command: a `cmd_*` function and its parser entry in `cli.py`, which only parses, prints
  and wires. The logic goes in `organize/`, `export/` or `sync/`.
- A new sampler layout: a device profile in `config/devices/`, not code
  (`docs/adding-a-profile.md`).
- A new device family: one `Device` subclass in `sync/` (`docs/adding-a-device.md`). Planning,
  backup and sync above it are shared; don't fork them per device.
- Sizes, durations, estimates, CSV and the device lock: `util.py`. Look there before writing a helper.
- User docs: `docs/` (index `docs/README.md`), CLI guides in `docs/cli/`, app guides in
  `docs/app/`. Update the guide a change affects in the same PR. The README stays overview,
  safety and install.

## Tests are part of every change

- Every new feature, change to an existing feature, or bug fix ships with a test for it,
  new or updated, in the same PR. A PR without test changes says why in one line (for
  example "docs only").
- Prefer TDD: write the failing test first and watch it fail. For a bug fix, the first commit
  is a test that reproduces it.
- If you change behavior an existing test pins, update the test deliberately and say why in
  the PR. Never delete, skip or loosen a test to get green.
- Enough tests, not more. Test the behavior someone relies on and the guards that protect
  their files, not implementation details. Test each behavior once, at the lowest layer that
  can catch it. When you touch an area, merge or delete tests that became redundant.
- Tests never read or write real libraries or anything under `~/sample-work`; use `tmp_path`.
- Layers, each owning one kind of risk:
  - **pytest** (the only layer that exists yet): logic and safety (plan, sync, guards, parsing, and the
    `--json` events once the app needs them), plus a few end-to-end runs against the fake `elektroid-cli` that unit tests
    can't reach. Extend the fake when you use a new device command or failure mode.
  - **Playwright**, once the desktop app exists: the UI does the right thing with what the
    CLI sends, and how it looks. Updating a screenshot baseline is its own commit.
  - **Small Rust and Vitest tests**: only for real branching outside Python (cancel, event
    parsing, layout math). None for components that only render props.

  The app's testing plan is under "Testing" in `docs/desktop-app-plan.md`.

## Writing

Applies to code comments, docs, READMEs, commit messages, PR descriptions and messages to Jules.

- Write like a person: plain, natural language. No AI-sounding phrases, filler, clichés or
  em-dashes.
- Be concise. Say it once and cut what doesn't add meaning.
- Prefer point form to long paragraphs. Use short headings when a doc covers more than one topic.
- Avoid jargon. When a technical term is needed, define it the first time and use it the
  same way after that.
- Use the same name for the same thing in code, comments and docs.
- Write for fresh eyes: the reader has none of your session or conversation context.
- Describe how things are now. No "previously", "as of last week" or "now uses X instead of
  Y"; history lives in git.
- Give the reader what they need to act: paths, links, issue numbers, specs.
- Code comments say why, not what. Skip comments that restate the code.

## Pull requests

- Work on a branch and open a PR to `main`. Every PR gets an agent review from a separate
  reviewer thread. The author answers or rebuts each comment, then merges once the review is
  resolved and tests pass. Jules doesn't need to review.
- Reviews are submitted as COMMENT (all agents share one GitHub account, which can't approve
  its own PR) with a bold "Reviewer verdict: approved" or "changes requested" line. That line
  is the verdict.
- Escalate to Jules only for what the rules above reserve: licensing, publishing, the
  device, new dependencies, breaking `scripts/`.
