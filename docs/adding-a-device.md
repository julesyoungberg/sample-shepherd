# Adding a device family

The sync layer talks to hardware through one small interface,
`sample_shepherd.sync.device.Device`. Backup, usage lists, planning and the resumable sync
are shared, so a new device family only needs a backend class.

## The interface

```python
class Device(ABC):
    project_suffix = ".xyzprj"     # file suffix of a project backup
    strips_extension = True        # does the device drop ".wav" from names on upload?

    def list_devices(self) -> list[DeviceInfo]: ...
    def info(self) -> dict: ...                       # optional: {"filesystems": [...]}
    def ls(self, path) -> list[Entry]: ...            # one folder; DeviceError if missing
    def ls_if_exists(self, path): ...                 # optional: ls or None, no retries
    def mkdir(self, path) -> None: ...                # with parents
    def upload(self, local, dest_dir) -> None: ...    # must never overwrite
    def delete(self, path) -> None: ...
    def list_projects(self) -> list[ProjectSlot]: ...
    def download_project(self, slot, dest_dir) -> Path: ...
```

`Entry` carries kind (`D`/`F`), name, size and an optional content hash. Paths start at the
sample storage's root, with `/` separators.

## Steps

1. Write `src/sample_shepherd/sync/<family>.py` with a `Device` subclass. If it drives an
   external program, take a `runner` argument (like `ElektronDevice`) so tests can replace
   the subprocess.
2. Register it in `get_backend()` in `sync/device.py` under a `[device] backend` name.
3. If its project backups list their samples differently from Elektron's `manifest.json`,
   extend `sync/projects.py`. **A project whose sample list can't be read must be an error,
   never an empty list**: an empty list would make every sample look deletable.
4. Tests: copy `tests/fake/elektroid-cli`'s approach. A fake program or runner backed by a
   temporary folder lets the full `listing → backup → used → plan → sync` flow run in
   pytest with no hardware.
5. Measure its transfer speed once and note it in the README's devices table, so users can
   set `[transfer]` for realistic estimates.

## Candidates

Elektroid also supports SDS samplers and others through other connectors (`sds:sample:...`),
which could become a second backend on the same program.
