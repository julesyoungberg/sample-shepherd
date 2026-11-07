# sample-shepherd documentation

Start with the [README](../README.md): what sample-shepherd is, the safety rules, and how to
install it. These pages go further.

## Using the command line

1. [Getting started](cli/getting-started.md): from sample packs to a synced Digitakt II, one
   step at a time.
2. [Configuration](cli/configuration.md): the config file, where it's looked up, and every
   setting.
3. [Commands](cli/commands.md): what each command is for, what it reads and writes, and how
   it keeps your device and projects safe.
4. [Command reference](cli/reference.md): every command and flag, generated from the code.

## Desktop app

Not built yet; the plan is in `desktop-app-plan.md`. Its guides will go in `docs/app/`, one
page per task, with screenshots in `docs/app/images/`, next to the CLI pages above.

## Extending it

- [Adding a device profile](adding-a-profile.md): render for a sampler or layout we don't ship.
- [Adding a device family](adding-a-device.md): sync to something other than Elektron.
- [Our patches to Fourier](fourier-patches.md): what each does and whether it can go upstream.

## Background

How the first library was built, and the research behind the design. Useful for history,
not needed to use the tool.

- [Fourier and Elektroid research](research-fourier-elektroid.md)
- [Working notes](working-notes.md), and the phase reports and plans:
  [0](phase0-report.md), [1](phase1-report.md), [2](phase2-report.md),
  [2b plan](phase2b-plan.md), [2b](phase2b-report.md), [2c plan](phase2c-plan.md),
  [device session 1 checklist](device-session-1-checklist.md)
