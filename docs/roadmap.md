# Roadmap

Planned work that isn't started or isn't finished.

## Desktop app

- Build it as planned in [desktop-app-plan.md](desktop-app-plan.md), starting with the
  style sheet page where the look gets chosen.
- Once screens exist: screenshots in the README, and step-by-step app guides with
  screenshots in `docs/app/`, generated from the Playwright fixtures.

## Landing page

A first version is in [site/](../site/README.md), not deployed. Still to do:

- Real screenshots and a demo video, once the app exists.
- App download links, once there's a build.
- Pick and connect a contact form service and a donation service.
- Pick hosting and a domain, then deploy.

## Publishing

- Publish the CLI to PyPI so `pipx install sample-shepherd` and `uv tool install
  sample-shepherd` work. Check the name is free first. Maybe Homebrew later.
- Choose a license, then open-source the repository.

## Ideas

- A TUI or small web page for reviewing plans.
- More devices: SDS samplers, which Elektroid supports.
- Record the measured transfer speed per device.
