# Configuration

sample-shepherd works without a config file: every setting has a default. You'll want one
to say where `elektroid-cli` and Fourier are, and where your backups and plans should go.

```bash
sample-shepherd config init             # writes ~/.config/sample-shepherd/config.toml
sample-shepherd config init --dry-run   # just says where it would write
sample-shepherd config show             # the file in effect and every resolved setting
```

`config init` copies [examples/sample-shepherd.toml](../../examples/sample-shepherd.toml),
which has a comment on every setting, and never overwrites an existing file. Run
`config show` after any edit to check the result.

## Where the file is looked up

The first of these that exists wins; the others are ignored, not merged.

1. `--config PATH`
2. `$SAMPLE_SHEPHERD_CONFIG`
3. `sample-shepherd.toml` in the current folder (handy for one config per library)
4. `$XDG_CONFIG_HOME/sample-shepherd/config.toml` (`~/.config/...` by default)

`--config` and `$SAMPLE_SHEPHERD_CONFIG` must point at a file that exists, so a typo fails
loudly instead of silently falling back. A setting the file doesn't know is an error too.

## Settings

Paths can use `~` and `$VARS`. Relative paths are read from the config file's folder, not
the folder you run the command in.

| Setting | Default | What it's for |
|---|---|---|
| `work_dir` | the current folder | Where backups go when a command isn't given a path (`projects backup` writes `<work_dir>/backups/<date>`). |
| `[device] backend` | `"elektron"` | The device family. Elektron (through `elektroid-cli`) is the only one so far. |
| `[device] id` | `1` | The device number from `sample-shepherd device ls`. `0` is the computer itself. |
| `[elektroid] cli` | `"elektroid-cli"` | A name on `PATH`, or the path to the one you built. |
| `[fourier] command` | `"fourier"` | A name on `PATH`, or the patched build from `organize install-fourier` (`<dir>/.venv/bin/fourier`). |
| `[fourier] env` | none | Environment for every Fourier run, usually `FOURIER_HOME` (its database and state) and `FOURIER_CONFIG` (your Fourier config). |
| `[export] profile_dirs` | none | Extra folders of device profiles, searched before the bundled ones. See [adding a profile](../adding-a-profile.md). |
| `[sync] protected` | `["/factory"]` | Device paths `plan` never deletes from. Add your own recordings and anything that lives only on the device. |
| `[transfer] bytes_per_second` | `77000` | Transfer speed, for time estimates only. |
| `[transfer] seconds_per_call` | `1.6` | Fixed cost per `elektroid-cli` call, for estimates only. `sync` prints your measured speed; put it here. |

## Flags override the file

`--work-dir`, `--device` and `--elektroid-cli` override their settings for one run. They go
before the command:

```bash
sample-shepherd --device 2 device info
```

## Environment variables

| Variable | Effect |
|---|---|
| `SAMPLE_SHEPHERD_CONFIG` | The config file (step 2 above). |
| `SAMPLE_SHEPHERD_LOCK_DIR` | Where the per-device lock file goes. Default `$XDG_RUNTIME_DIR`, else the system temp folder. Every sample-shepherd process that shares a device must use the same folder. |

A fuller real-world example: [examples/original-build.toml](../../examples/original-build.toml),
the config the first Digitakt II library build used.
