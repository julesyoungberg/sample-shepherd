# CLAUDE.md

Notes for Claude (and anyone else) working in this repo.

## Tests are part of every change

- Every new feature, bug fix, or behavior change adds or updates tests **in the same PR**.
  A PR that changes behavior without touching tests needs a one-line reason in its
  description (for example "docs only" or "pure refactor, covered by `tests/test_plan.py`").
- Prefer test-driven development: write the failing test first, watch it fail, then make it
  pass. For a bug fix, the first commit is a test that reproduces the bug.
- If you change behavior an existing test pins down, update the test deliberately and say
  why in the PR. Never delete, skip, or loosen a test just to get green.
- Run `pytest` before you push. It must pass with no device attached.

### Which layer

Put each test in the cheapest layer that can catch the problem. Today only the Python
layers exist; the rest arrive with the desktop app (see `docs/desktop-app-plan.md`,
"Testing"), and this rule applies to them as soon as they do.

1. **Unit:** pytest for the CLI (`tests/`); `cargo test` and Vitest for the app.
2. **Contract:** the `--json` event schema. If you change an event, update the schema, the
   generated UI types, and the recorded streams together.
3. **Closed loop:** the real CLI against the fake `elektroid-cli` (`tests/fake/`). Extend
   the fake when you use a new device command or failure mode.
4. **End-to-end UI:** Playwright flows with mocked Tauri IPC.
5. **Screenshot:** Playwright `toHaveScreenshot`. Changing a baseline is its own deliberate
   commit that the reviewer looks at.

### Never touch a real device or real files

- Tests never call the real `elektroid-cli`, never talk to a connected Elektron device, and
  never read or write real sample libraries, the Ableton User Library, or anything under
  `~/sample-work`. Use `tmp_path` and the fake `elektroid-cli`.
- Generate audio at test time (see `make_wav` in `tests/conftest.py`). Never commit audio.
