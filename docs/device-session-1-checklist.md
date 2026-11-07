# Device session 1: back up, then capture what's on the Digitakt II

**Goal:** a safe backup of every project, plus three things captured for Phase 3: the +Drive
listing, its free space, and each project's sample list.

**Not in this session:** nothing gets uploaded, deleted, moved or renamed on the device, and no
project is saved over. The final sync is session 2.

Items marked **(verify)** are facts I couldn't check without the device or its current manuals.
Note what you find, and I'll fold it into the plan.

Everything you capture goes under `~/sample-work/device/`:

```
device/
  backups/          project backups (two copies: this folder and an external drive)
  drive/            a copy of the +Drive's files, if Transfer can download them (best input)
  drive-listing.csv the +Drive listing, if no folder copy: path,size[,seconds]
  projects/         one <project name>.txt per project: its +Drive sample paths, one per line
  notes.md          OS version, free space, answers to the (verify) items
```

## 1. Before you start

- [ ] Note the Digitakt II OS version. Fourier's profile is based on manual OS 1.16 (2026-09-09).
- [ ] Update Elektron Transfer on the Mac to its current version.
- [ ] Check which backup tools support the **Digitakt II**, not only the original Digitakt **(verify)**:
  - Elektron Transfer: project backup?
  - elk-herd: its site lists the devices it supports.
  - SysEx dump from the device, received with Elektron C6 or elk-herd.
- [ ] Confirm `~/sample-work/device/` and an external drive both have room. The +Drive is 20 GB
  (manual p.29), so a full copy can be up to that size.

## 2. Back up every project (do this first)

- [ ] Back up every project with the tool that supports the Digitakt II. Prefer one that keeps
  the project's sample references, not just its patterns **(verify what each tool includes)**.
- [ ] Save into `device/backups/` with the date in the name, then copy to the external drive.
- [ ] Check that each backup file exists, isn't 0 bytes, and is listed by the tool that made it.
  **Don't test a backup by restoring it to the device.** A restore overwrites the project on the device.
- [ ] Write in `notes.md`: the tool and version, each file's name, size and date, and which projects it covers.

## 3. Capture the +Drive listing (read-only)

Best: a copy of the +Drive's files on the Mac, if Transfer can download the whole +Drive or
folder by folder **(verify)**. Copying from the device only reads it.

- [ ] Download into `device/drive/`, keeping the +Drive's folder structure. The Phase 3 scripts
  then read sizes and durations, and hash the files themselves.
- [ ] If there's no download, write `device/drive-listing.csv` instead. Columns: `path,size`,
  plus `seconds` if you can see it. Paths start from the +Drive root, e.g. `/Drums/909/BD 01.wav`.
  A listing with names only works too, but then many samples will match nothing (KEEP-UNMATCHED),
  because a name alone is never treated as proof.
- [ ] Note the **free space** and total used, as the device or Transfer shows them.

## 4. Capture each project's sample list

- [ ] For each project, list the +Drive samples it uses in `device/projects/<project>.txt`, one
  path per line, written exactly as in the +Drive listing. Possible sources **(verify which works
  on the Digitakt II)**:
  - elk-herd's project view,
  - the project's sample pool on the device,
  - whatever the backup tool shows.
- [ ] If a tool only shows sample *names*, not paths, write the names one per line and say so in
  `notes.md`. I'll match on names plus the +Drive listing, and flag anything ambiguous instead of guessing.

## 5. While you're there: facts to note (read-only)

- [ ] **(verify)** The longest sample name the device shows in full: does it cut long names, and where?
  Fourier's profile leaves the name length unchecked.
- [ ] **(verify)** Whether the browser opens folders inside folders, e.g. an existing nested folder
  if you have one. This matters for a possible third folder level. Don't create any folders for this.
- [ ] Don't try SEL FOR MOVE / MOVE HERE in this session. Whether moves keep project links is
  unverified, and we'll only investigate it on backed-up copies, in Phase 3.

## 6. After the session

Tell me it's done. I'll then:
1. check the backups and inputs for completeness,
2. run `scripts/project_coverage.py` and `scripts/delete_list.py`, which are read-only,
3. send you the coverage report and the delete-list CSV (SAFE / KEEP-USED / KEEP-UNMATCHED) for
   you to review. You delete by hand, after checking.
