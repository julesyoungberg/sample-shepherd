# Landing page

The public page for sample-shepherd: what it does, how to install it, supported devices,
tutorials, FAQ, changelog, privacy and credits. It's not deployed anywhere yet.

## Run it

```bash
cd site
pnpm install
pnpm dev        # http://localhost:5173, reloads as you edit
pnpm build      # static files in site/build/, ready for any static host
```

## Where things are

- `src/lib/content.js`: all the words and lists (features, devices, FAQ, changelog,
  credits). Edit text here.
- `src/routes/+page.svelte`: the layout, one section per heading.
- `src/app.css`: the design tokens (paper, ink, one signal color), shared in spirit with
  the desktop app's "field manual" direction in `docs/desktop-app-plan.md`.

## Why this stack

SvelteKit with `adapter-static` and Tailwind v4, the same tools the desktop app plan picks.
The page builds to plain HTML and CSS with no server, and the app's tokens and components
can be reused here later. No analytics, cookies, or third-party fonts or scripts: the font
is bundled from npm.

## Placeholders

These are marked "coming soon" on the page. Each needs an outside service, so none
is set up yet:

- Screenshots and the demo video: wait for the desktop app.
- The download button: waits for the first app build.
- The contact form: not connected to any form service; it can't send.
- The donate link: no donation service chosen.
- The license line in the footer: the repo has no license yet.

Links to files in the repo (`repoFile(...)` in `content.js`) are checked by
`tests/test_site_links.py`, so moving a doc fails the tests instead of breaking the page.
