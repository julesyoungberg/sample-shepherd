# Commands

What each command is for, what it reads and writes, and the checks that keep your device
and its projects safe. Every flag is in the [command reference](reference.md);
[Getting started](getting-started.md) runs them in order.

## At a glance

| Command | What it does | Writes / touches |
|---|---|---|
| `config show` / `config init` | Settings in effect / write a starter config | `init`: the config file (never overwrites) |
| `organize doctor` | Is Fourier installed and configured? | nothing |
| `organize build` | Runs `fourier build` | Fourier's outputs |
| `organize patches` | Lists our patches to Fourier | nothing |
| `organize install-fourier --dir D` | Clones Fourier at the base commit, applies the patches, `uv sync` | `D` (must not exist) |
| `export profiles` | Lists device profiles | nothing |
| `export render PROFILE` | Runs `fourier render` with our profiles | the output folder |
| `export check RENDER --profile P` | Checks a render against the profile's limits | nothing |
| `device ls` / `device info` | Connected devices / a device's filesystems | reads the device |
| `device listing --out CSV` | Lists the sample storage: `path,size,hash` | reads the device; writes `CSV` |
| `projects ls` | Lists project slots | reads the device |
| `projects backup` | Downloads projects, one folder per slot, plus `backup-index.csv` | reads the device; writes the backup folder |
| `projects used --backups DIR --out CSV` | Samples the backed-up projects use | `CSV` |
| `plan ... --out CSV` | Works out what to upload and delete | `CSV` |
| `sync --plan CSV` | Carries out a plan, logging each step | **the device** |

## Rules every command follows

- **`--dry-run` changes nothing.** Every command that writes a file or touches a device
  has it. See [dry runs and the device](#dry-runs-and-the-device) for which ones still read
  the device.
- **Nothing deletes without `--yes`.** Only `sync` deletes, and only rows of a plan you've
  written and can read.
- **One device user at a time.** Commands that talk to a device hold a per-device lock and
  stop with an error if another sample-shepherd process has it. They can't see other
  programs: close Elektron Transfer and don't run `elektroid-cli` by hand meanwhile.
- **Your source library is read-only.** Fourier reads it; nothing writes to it.

## config

`config init` writes the starter config and refuses if the file exists. `config show`
prints every resolved setting and which file they came from. See
[Configuration](configuration.md).

## organize

A thin layer over [Fourier Samples](https://github.com/bvk7787/fourier-samples), run as a
separate program with the environment from `[fourier] env`.

- `organize doctor` finds the `fourier` command and runs `fourier --version`. It exits 1 if
  Fourier isn't found, with the two ways to install it.
- `organize install-fourier --dir D` prints its steps (clone, apply our patches, `uv sync`),
  then runs them. `D` must not exist. With `--dry-run` it only prints the steps.
- `organize build` runs `fourier build`; with `--dry-run`, Fourier's own dry run, which
  writes nothing. Extra Fourier arguments go after `--`.
- `organize patches` lists [our patches](../fourier-patches.md) to Fourier.

## export

- `export profiles` lists every profile: yours from `[export] profile_dirs` first, then the
  bundled ones.
- `export render PROFILE` runs `fourier render` with our profiles. It stops early on an
  unknown profile name. `--from` and `--out` default to Fourier's config.
- `export check RENDER --profile P` reads the render and reports what the device would
  refuse or hide: too many files in a folder, folders too deep, the wrong sample rate or
  bit depth, and (for Elektron profiles) names over 32 characters. It exits 1 if it finds
  anything, so it works in scripts.

## device

All read-only.

- `device ls`: connected devices and their numbers. Put the number in `[device] id`.
- `device info`: the device's filesystems. Without a `sample` filesystem, sample sync
  isn't supported (see [supported devices](../../README.md#supported-devices)).
- `device listing --out CSV`: every file in the sample storage with its size and content
  hash. `plan` reads it. `--root` lists one folder only.

## projects

- `projects ls`: the project slots on the device.
- `projects backup`: downloads every project into `<out>/<slot>/`, with
  `backup-index.csv` (SHA-256 of each file) and the device's full slot list. Each project
  downloads into a `.part` folder and is renamed when complete, so a stopped backup never
  leaves a half-written project. Run it again to finish: it skips slots already backed up.
  `--slots` backs up only some slots, and doesn't write the slot list. Copy the backup off
  your computer, and **never test a backup by restoring it**: a restore overwrites the
  project on the device.
- `projects used --backups DIR --out CSV`: reads the backups (not the device) and lists
  every sample the projects use, by path and content hash. It **refuses a backup that
  can't be shown to hold every slot**, because samples only a missing project uses would
  look deletable. `--allow-partial` overrides that; use it only if you're sure. It also
  stops on a project whose package has no sample list, rather than treating it as "uses
  nothing".

## plan

Reads a listing, an export and the project usage, and writes a plan CSV. It doesn't touch
the device.

### How `plan` decides

- **Upload** each export file whose device path (folder plus name, no extension) isn't on the
  device. `--folders` limits it to some top-level folders, and `--dest` puts them under a device
  folder.
- **Delete candidates** come only from what you ask for: `--prune` (device files inside the
  synced folders that the export doesn't have), and `--replace CSV` (a list of device paths,
  for example from your own matching). Without either, the plan only uploads.
- A candidate is **kept** if a project uses it (same path, ignoring case, or the same content
  hash), or if it's under a protected path (`[sync] protected`, `/factory` by default).
  `--prune` and `--replace` need `--used`: without it, or with an empty one, `plan` stops
  with an error.
- Every row is in the CSV with its reason (and, for delete candidates, the device's content
  hash): `upload`, `delete`, `skip-exists`, `keep-used`, `keep-protected`, `skip-missing`.
  You can delete rows before syncing. A delete row you add by hand needs its `hash` from the
  listing, or `sync` refuses it.

With `--prune`, the folders you name with `--folders` are the delete scope. Name category
folders under their section (`DRUMS/01_KICKS`), not a whole section: `--folders DRUMS` would
make all of `/DRUMS` on the device fair game. If you keep your own folders called `DRUMS`,
`FX`, `LOOPS`, `TONAL` or `VOX` (ignoring case), always pass `--folders` with `--prune`.

`plan` prints a summary with a time estimate from `[transfer]`.

## sync

Carries out a plan on the device.

- **Uploads first, deletes last.** Deletes run only after every upload in the plan has
  succeeded.
- **Uploads never overwrite.** A file whose name is already in its device folder is skipped.
- **Deletes need `--yes` and `--used`.** Without `--yes`, `sync` lists the deletes and
  stops. Each delete is checked again the way `plan` checks it (protected paths, paths and
  content hashes projects use), and a delete row without the content hash from the listing
  is refused, so a stale or hand-edited plan can't slip one through. Refused deletes are
  logged and skipped, and don't change the exit code. `--no-delete` runs only the uploads.
- **Resumable.** Each step is logged to `<plan>-log.csv` (or `--log`). Stop it any time
  (Ctrl-C, a dropped cable) and run the same command again: it skips what the log lists as
  done. After 20 failed steps it stops; fix the cause and rerun.

`sync --dry-run` prints the summary and time estimate and sends nothing.

## Dry runs and the device

`--dry-run` never changes anything. For `device ls`, `device info` and `projects ls` it
doesn't contact the device either; it prints the `elektroid-cli` command it would run.
`device listing --dry-run` and `projects backup --dry-run` do read the device (one folder
listing, the project list) to give you counts and a time estimate, so don't run them while
another program is transferring.

## Exit codes

| Code | Meaning |
|---|---|
| 0 | Done. |
| 1 | Finished, but found problems: `export check` issues, failed `sync` steps, Fourier not found. |
| 2 | Stopped with an error: a usage error, a missing file, deletes without `--yes` or `--used`, the device lock held, or `sync` stopping after 20 failures. The message says what to fix. |
| 3 | The device returned an error. |
| 130 | Interrupted. Logged work is kept; rerun to resume. |
