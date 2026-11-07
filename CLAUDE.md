# CLAUDE.md

Notes for Claude (and anyone else) working in this repo.

## Tests are part of every change

- Every new feature, bug fix, or behavior change adds or updates tests **in the same PR**.
  A behavior change always comes with tests. A PR that doesn't add or update tests says
  why in one line in its description (for example "docs only" or "pure refactor, covered
  by `tests/test_plan.py`").
- Prefer test-driven development: write the failing test first, watch it fail, then make it
  pass. For a bug fix, the first commit is a test that reproduces the bug.
- If you change behavior an existing test pins down, update the test deliberately and say
  why in the PR. Never delete, skip, or loosen a test just to get green.
- Run the tests before you push (`.venv/bin/pytest` or `uv run pytest`, as in the README).
  They must pass with no device attached.

### Enough tests, not more

Don't over-engineer, here or anywhere: think like a senior engineer and aim for sufficient
coverage, not maximum. Test the behavior someone relies on and the guards that protect
their files, not implementation details. Test each behavior once, at the lowest layer that
can catch it, and don't re-test it at higher layers or in slightly different ways. Higher
layers cover only what lower ones can't see (wiring between processes, real UI flows). When
you touch an area, delete or merge tests that have become redundant.

### Which layer

Today only pytest exists (`tests/`, including the closed loop against the fake
`elektroid-cli` in `tests/fake/`). The desktop app adds the others; see "Testing" in
`docs/desktop-app-plan.md`. Each layer owns one kind of risk:

- **pytest:** logic and safety (plan, sync, guards, parsing, `--json` output), plus a
  few end-to-end scenarios against the fake `elektroid-cli` that unit tests can't reach.
  Extend the fake when you use a new device command or failure mode.
- **Playwright:** the UI does the right thing with what the CLI sends, and how it looks
  (screenshots). It trusts pytest for whether the plan is right. Updating a screenshot
  baseline is its own deliberate commit.
- **Small Rust and Vitest unit tests:** only for real branching outside Python (cancel,
  event parsing, layout math). No tests for components that only render props.

### Never touch a real device or real files

- Tests never call the real `elektroid-cli`, never talk to a connected Elektron device, and
  never read or write real sample libraries, the Ableton User Library, or anything under
  `~/sample-work`. Use `tmp_path` and the fake `elektroid-cli`.
- Trying something on a real device by hand isn't a test. It happens only after Jules says
  the live sync is finished, follows `docs/device-session-1-checklist.md`, and never runs
  in CI.
- Generate audio at test time (see `make_wav` in `tests/conftest.py`). Never commit audio.
