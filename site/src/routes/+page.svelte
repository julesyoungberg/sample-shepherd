<script>
  import {
    REPO,
    repoFile,
    pitch,
    features,
    screenshots,
    devices,
    docs,
    faq,
    changelog,
    credits
  } from '$lib/content.js';

  const sections = [
    ['features', 'Features'],
    ['install', 'Install'],
    ['devices', 'Devices'],
    ['docs', 'Tutorials'],
    ['faq', 'FAQ'],
    ['changelog', 'Changelog']
  ];

  const install = `uv tool install git+${REPO}
# or: pipx install git+${REPO}
sample-shepherd --help`;
</script>

<svelte:head>
  <title>sample-shepherd: sync your sample library to your sampler, safely</title>
  <meta name="description" content={pitch} />
</svelte:head>

<header class="border-b border-rule">
  <nav class="mx-auto flex max-w-5xl flex-wrap items-center gap-x-6 gap-y-2 px-4 py-3">
    <a href="#top" class="font-mono font-bold no-underline">sample-shepherd</a>
    <ul class="flex flex-wrap gap-x-4 gap-y-1 text-sm">
      {#each sections as [id, name]}
        <li><a href="#{id}" class="no-underline">{name}</a></li>
      {/each}
    </ul>
    <a href={REPO} class="ml-auto text-sm">GitHub</a>
  </nav>
</header>

<main id="top" class="mx-auto max-w-5xl px-4">
  <!-- Pitch and demo -->
  <section class="grid gap-8 border-b border-rule py-16 md:grid-cols-2 md:items-center">
    <div>
      <p class="label">For Elektron samplers and the people who fill them</p>
      <h1 class="mt-3 text-4xl font-semibold tracking-tight md:text-5xl">
        Your sample library, on every device, without breaking a project.
      </h1>
      <p class="mt-5 text-lg text-ink-soft">{pitch}</p>
      <div class="mt-8 flex flex-wrap gap-3">
        <a href="#download" class="bg-ink px-5 py-2.5 font-medium text-paper no-underline hover:bg-signal hover:text-ink">
          Download
        </a>
        <a href="#install" class="border border-ink px-5 py-2.5 font-medium no-underline">
          Install the command line tool
        </a>
      </div>
    </div>
    <figure>
      <div class="hatch flex aspect-video items-center justify-center border border-rule">
        <span class="label bg-paper px-2">Demo video coming soon</span>
      </div>
      <figcaption class="label mt-2">Demo: from sample packs to a synced Digitakt II</figcaption>
    </figure>
  </section>

  <!-- Features -->
  <section id="features" class="border-b border-rule py-16">
    <p class="label">01 Features</p>
    <h2 class="mt-2 text-3xl font-semibold">Careful by default</h2>
    <div class="mt-8 grid border-t border-l border-rule sm:grid-cols-2 lg:grid-cols-3">
      {#each features as f, i}
        <div class="border-r border-b border-rule p-5">
          <p class="label">{String(i + 1).padStart(2, '0')}</p>
          <h3 class="mt-2 font-semibold">{f.title}</h3>
          <p class="mt-2 text-sm text-ink-soft">{f.body}</p>
        </div>
      {/each}
    </div>
  </section>

  <!-- Screenshots: placeholders until the desktop app exists -->
  <section id="screenshots" class="border-b border-rule py-16">
    <p class="label">02 Screenshots</p>
    <h2 class="mt-2 text-3xl font-semibold">The desktop app</h2>
    <p class="mt-3 text-ink-soft">In progress. Screenshots will go here once the first screens are built.</p>
    <div class="mt-8 grid gap-6 md:grid-cols-3">
      {#each screenshots as s}
        <figure>
          <div class="hatch flex aspect-[4/3] items-center justify-center border border-rule">
            <span class="label bg-paper px-2">{s.title}</span>
          </div>
          <figcaption class="mt-2 text-sm text-ink-soft">{s.caption}</figcaption>
        </figure>
      {/each}
    </div>
  </section>

  <!-- Download and install -->
  <section id="download" class="grid grid-cols-1 gap-10 border-b border-rule py-16 md:grid-cols-2">
    <div>
      <p class="label">03 Download</p>
      <h2 class="mt-2 text-3xl font-semibold">Desktop app</h2>
      <p class="mt-3 text-ink-soft">Not released yet. macOS on Apple silicon comes first.</p>
      <button disabled class="mt-6 cursor-not-allowed border border-rule px-5 py-2.5 text-ink-soft">
        Download for macOS (coming soon)
      </button>
    </div>
    <div id="install" class="min-w-0">
      <p class="label">04 Install</p>
      <h2 class="mt-2 text-3xl font-semibold">Command line tool</h2>
      <p class="mt-3 text-ink-soft">
        Needs Python 3.11 or newer and <a href="https://docs.astral.sh/uv/">uv</a> (or pipx). Syncing
        to a device also needs <code class="font-mono">elektroid-cli</code>; the
        <a href={repoFile('README.md')}>README</a> shows how to install it.
      </p>
      <pre class="mt-5 overflow-x-auto border border-rule p-4 font-mono text-sm"><code>{install}</code></pre>
    </div>
  </section>

  <!-- Supported devices -->
  <section id="devices" class="border-b border-rule py-16">
    <p class="label">05 Supported devices</p>
    <h2 class="mt-2 text-3xl font-semibold">Elektron first</h2>
    <div class="mt-8 overflow-x-auto">
      <table class="w-full min-w-[32rem] text-left text-sm">
        <thead class="label">
          <tr class="border-b border-ink">
            <th class="py-2 pr-4 font-normal">Device</th>
            <th class="py-2 pr-4 font-normal">Sample sync</th>
            <th class="py-2 font-normal">Project backup</th>
          </tr>
        </thead>
        <tbody>
          {#each devices as d}
            <tr class="border-b border-rule">
              <td class="py-2 pr-4 font-medium">
                {d.name}{#if d.tested}<span class="label ml-2 text-signal">tested on hardware</span>{/if}
              </td>
              <td class="py-2 pr-4">{d.sync}</td>
              <td class="py-2">{d.backup}</td>
            </tr>
          {/each}
        </tbody>
      </table>
    </div>
    <p class="mt-4 text-sm text-ink-soft">
      Export works for any sampler that reads folders of WAV files, such as Ableton Live or XO.
      Want another device? See <a href={repoFile('docs/adding-a-device.md')}>adding a device</a>.
    </p>
  </section>

  <!-- Tutorials -->
  <section id="docs" class="border-b border-rule py-16">
    <p class="label">06 Tutorials</p>
    <h2 class="mt-2 text-3xl font-semibold">Learn it step by step</h2>
    <ul class="mt-8 grid gap-6 sm:grid-cols-2">
      {#each docs as d}
        <li>
          <a href={repoFile(d.path)} class="font-semibold">{d.title}</a>
          <p class="mt-1 text-sm text-ink-soft">{d.body}</p>
        </li>
      {/each}
    </ul>
    <p class="mt-6 text-sm"><a href={repoFile('docs/README.md')}>All documentation</a></p>
  </section>

  <!-- FAQ -->
  <section id="faq" class="border-b border-rule py-16">
    <p class="label">07 FAQ</p>
    <h2 class="mt-2 text-3xl font-semibold">Questions</h2>
    <div class="mt-8 divide-y divide-rule border-y border-rule">
      {#each faq as item}
        <details class="group py-4">
          <summary class="cursor-pointer font-medium">{item.q}</summary>
          <p class="mt-2 text-ink-soft">{item.a}</p>
        </details>
      {/each}
    </div>
  </section>

  <!-- Changelog -->
  <section id="changelog" class="border-b border-rule py-16">
    <p class="label">08 Changelog</p>
    <h2 class="mt-2 text-3xl font-semibold">What's new</h2>
    {#each changelog as release}
      <div class="mt-8 grid gap-2 md:grid-cols-[10rem_1fr]">
        <p class="font-mono">{release.version}<br /><span class="label">{release.date}</span></p>
        <ul class="list-disc space-y-1 pl-5 text-ink-soft">
          {#each release.notes as note}<li>{note}</li>{/each}
        </ul>
      </div>
    {/each}
  </section>

  <!-- Contact and support: placeholders, no service is connected -->
  <section id="contact" class="grid gap-10 border-b border-rule py-16 md:grid-cols-2">
    <div>
      <p class="label">09 Contact</p>
      <h2 class="mt-2 text-3xl font-semibold">Get in touch</h2>
      <p class="mt-3 text-sm text-ink-soft">This form isn't connected yet, so messages aren't sent anywhere.</p>
      <form class="mt-6 space-y-4" onsubmit={(e) => e.preventDefault()}>
        <label class="block">
          <span class="label">Email</span>
          <input type="email" disabled class="mt-1 block w-full border border-rule bg-transparent px-3 py-2" />
        </label>
        <label class="block">
          <span class="label">Message</span>
          <textarea rows="4" disabled class="mt-1 block w-full border border-rule bg-transparent px-3 py-2"></textarea>
        </label>
        <button type="submit" disabled class="cursor-not-allowed border border-rule px-5 py-2.5 text-ink-soft">
          Send (coming soon)
        </button>
      </form>
    </div>
    <div>
      <p class="label">10 Support</p>
      <h2 class="mt-2 text-3xl font-semibold">Support the work</h2>
      <p class="mt-3 text-ink-soft">
        sample-shepherd is free. If it saves you time, a donation helps keep it going.
      </p>
      <span class="mt-6 inline-block cursor-not-allowed border border-rule px-5 py-2.5 text-ink-soft">
        Donate (coming soon)
      </span>
    </div>
  </section>

  <!-- Privacy -->
  <section id="privacy" class="py-16">
    <p class="label">11 Privacy</p>
    <h2 class="mt-2 text-3xl font-semibold">Your samples stay yours</h2>
    <ul class="mt-6 max-w-3xl list-disc space-y-2 pl-5 text-ink-soft">
      <li>No account, no telemetry. sample-shepherd runs on your computer and reads your library there.</li>
      <li>Your source library is read-only: nothing writes to it.</li>
      <li>It goes online only to install tools you ask for, such as Fourier Samples from GitHub, and when Fourier downloads its sorting model.</li>
      <li>This site sets no cookies, has no analytics, and loads no third-party scripts or fonts.</li>
    </ul>
  </section>
</main>

<footer class="border-t border-ink">
  <div class="mx-auto grid max-w-5xl gap-8 px-4 py-10 text-sm md:grid-cols-[1fr_2fr]">
    <div>
      <p class="font-mono font-bold">sample-shepherd</p>
      <p class="mt-2 text-ink-soft">By Jules Youngberg. License to be announced.</p>
      <p class="mt-2"><a href={REPO}>Source on GitHub</a></p>
    </div>
    <div>
      <p class="label">Credits</p>
      <ul class="mt-3 space-y-3">
        {#each credits as c}
          <li>
            <a href={c.url}>{c.name}</a> <span class="label">{c.license}</span>
            <p class="text-ink-soft">{c.note}</p>
          </li>
        {/each}
      </ul>
    </div>
  </div>
</footer>
