# Adding a device profile

A profile says how a render is laid out for one target: folder depth, files per folder,
sample rate, bit depth and so on. Profiles are YAML in Fourier's own format, so the same
file drives `fourier render` and sample-shepherd's `export check`.

## 1. Start from the closest existing profile

`sample-shepherd export profiles` lists what's found. Most profiles only change a few
values of a base with `extends:`. For example, the bundled
[digitakt_2_50.yaml](../config/devices/digitakt_2_50.yaml):

```yaml
id: digitakt_2_50
extends: digitakt_2          # Fourier's own profile: 48 kHz/16-bit, depth 2, ...
name: Elektron Digitakt 2 (50 files a folder)
paths:
  files_per_folder: {value: 50, status: convention}
```

Each value is `{value: ..., status: ...}`. `status` says where it comes from: `convention`
(your choice), `unverified` (a guess), or a cited fact (Fourier's base profiles cite manual
pages). The fields Fourier reads are documented in its `docs/device-profiles.md`.

## 2. Put it where sample-shepherd and Fourier both find it

Save it as `<id>.yaml` in a folder of your own and list that folder in your config:

```toml
[export]
profile_dirs = ["~/my-profiles"]
```

`export render` passes the first profile folder to Fourier as `FOURIER_DEVICES` unless your
`[fourier] env` sets it. To ship a profile with sample-shepherd itself, add it to
`config/devices/` in this repository.

## 3. Check it

```bash
sample-shepherd export profiles                         # it's listed
sample-shepherd export render my_sampler --dry-run      # the fourier command it would run
sample-shepherd export render my_sampler --out renders/my_sampler
sample-shepherd export check renders/my_sampler --profile my_sampler
```

`export check` resolves the `extends:` chain and checks files per folder, folder depth, and
each WAV's sample rate and bit depth. When Fourier's own base profile files aren't
readable, it falls back to the values in `BASE_FACTS` (`src/sample_shepherd/export/profiles.py`).

Mark anything you haven't checked on the hardware as `unverified` (for example a third
folder level, until you've seen the device's browser open it).
