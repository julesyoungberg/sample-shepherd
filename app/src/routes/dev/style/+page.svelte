<script lang="ts">
  import { categories } from '$lib/categories';
  import Waveform from '$lib/Waveform.svelte';

  // The one page Jules reviews for the look; every later screen reuses these pieces.
  const surfaces = ['paper', 'panel', 'ink', 'ink-soft', 'rule', 'signal'];
  const typeScale = [
    ['text-2xl', 'Library'],
    ['text-lg', 'Plan for Digitakt II'],
    ['text-base', 'Uploads 846 samples, keeps 71 that projects use.'],
    ['text-sm', 'Names over 32 characters are shortened on export.']
  ];
  const rows = [
    { name: 'KICK_TAPE_01.wav', category: 'kick', duration: '0.42', ch: 'mono', size: '74 KiB', action: 'upload' },
    { name: 'SNR_ROOM_B.wav', category: 'snare', duration: '0.61', ch: 'stereo', size: '214 KiB', action: 'keep' },
    { name: 'HAT_CLOSED_7.wav', category: 'hat', duration: '0.12', ch: 'mono', size: '21 KiB', action: 'delete' },
    { name: 'SUB_DRONE_C.wav', category: 'bass', duration: '2.80', ch: 'mono', size: '494 KiB', action: 'upload' },
    { name: 'VOX_CHOP_3.wav', category: 'vocal', duration: '1.05', ch: 'stereo', size: '371 KiB', action: 'keep' }
  ];

  // Seeded noise with a decaying envelope, so the waveform looks the same on every load.
  function fakePeaks(seed: number, n = 160) {
    let s = seed;
    const rand = () => ((s = (s * 16807) % 2147483647) / 2147483647);
    return Array.from({ length: n }, (_, i) => Math.exp(-i / 40) * (0.6 + 0.4 * rand()));
  }

  let theme: 'light' | null = $state(null);
  $effect(() => {
    if (theme) document.documentElement.dataset.theme = theme;
    else delete document.documentElement.dataset.theme;
  });
</script>

<svelte:head><title>Style sheet · sample-shepherd</title></svelte:head>

<main class="mx-auto max-w-4xl space-y-12 p-8">
  <header class="flex items-baseline justify-between border-b border-rule pb-4">
    <div>
      <p class="label">Dev</p>
      <h1 class="text-2xl font-semibold">Style sheet</h1>
    </div>
    <div class="flex gap-2" role="group" aria-label="Theme">
      {#each [[null, 'Console'], ['light', 'Paper']] as const as [value, text]}
        <button class="btn" aria-pressed={theme === value} onclick={() => (theme = value)}>{text}</button>
      {/each}
    </div>
  </header>

  <section aria-labelledby="tokens">
    <h2 id="tokens" class="label">01 Surfaces</h2>
    <ul class="mt-4 grid grid-cols-3 gap-px border border-rule bg-rule sm:grid-cols-6">
      {#each surfaces as name}
        <li class="bg-paper p-2">
          <div class="h-10 border border-rule" style:background="var(--color-{name})" data-swatch={name}></div>
          <p class="mt-1 font-mono text-xs">{name}</p>
        </li>
      {/each}
    </ul>
  </section>

  <section aria-labelledby="type">
    <h2 id="type" class="label">02 Type</h2>
    <div class="mt-4 space-y-2">
      {#each typeScale as [size, text]}
        <p class={size}><span class="label mr-3 inline-block w-20">{size.slice(5)}</span>{text}</p>
      {/each}
      <p class="font-mono text-sm"><span class="label mr-3 inline-block w-20">mono</span>/kicks/01 KICKS/KICK_TAPE_01.wav · 1,204,224 B</p>
    </div>
  </section>

  <section aria-labelledby="categories">
    <h2 id="categories" class="label">03 Categories</h2>
    <ul class="mt-4 grid grid-cols-5 gap-2">
      {#each categories as cat, i}
        <li class="flex items-center gap-2 font-mono text-xs">
          <span class="inline-block h-4 w-4" style:background="var(--color-cat-{cat})" data-category={cat}></span>
          {String(i + 1).padStart(2, '0')} {cat.toUpperCase()}
        </li>
      {/each}
    </ul>
  </section>

  <section aria-labelledby="buttons">
    <h2 id="buttons" class="label">04 Buttons</h2>
    <div class="mt-4 flex flex-wrap gap-2">
      <button class="btn">Dry run</button>
      <button class="btn btn-signal">Upload 846</button>
      <button class="btn btn-signal"><span class="hatch-delete mr-2 inline-block h-2 w-4 align-middle"></span>Delete 12</button>
      <button class="btn" disabled>Device busy</button>
    </div>
  </section>

  <section aria-labelledby="inputs">
    <h2 id="inputs" class="label">05 Inputs</h2>
    <div class="mt-4 flex flex-wrap items-center gap-4">
      <label class="flex items-center gap-2 text-sm">Filter <input class="field" placeholder="kick tape" /></label>
      <label class="flex items-center gap-2 text-sm"><input type="checkbox" class="accent-ink" checked /> Stereo only</label>
      <label class="flex items-center gap-2 text-sm">Profile
        <select class="field"><option>digitakt-ii</option><option>model-samples</option></select>
      </label>
    </div>
  </section>

  <section aria-labelledby="table">
    <h2 id="table" class="label">06 Table</h2>
    <table class="mt-4 w-full border-collapse font-mono text-xs">
      <thead>
        <tr class="h-7 border-b border-ink text-left">
          <th class="label font-normal">Name</th><th class="label font-normal">Category</th>
          <th class="label text-right font-normal">Seconds</th><th class="label font-normal pl-4">Channels</th>
          <th class="label text-right font-normal">Size</th><th class="label font-normal pl-4">Plan</th>
        </tr>
      </thead>
      <tbody>
        {#each rows as row}
          <tr class="h-7 border-b border-rule hover:bg-panel">
            <td>{row.name}</td>
            <td><span class="mr-2 inline-block h-2 w-2" style:background="var(--color-cat-{row.category})"></span>{row.category}</td>
            <td class="text-right">{row.duration}</td>
            <td class="pl-4">{row.ch}</td>
            <td class="text-right">{row.size}</td>
            <td class="pl-4" class:text-signal={row.action !== 'keep'}>
              {#if row.action === 'delete'}<span class="hatch-delete mr-2 inline-block h-2 w-4 align-middle"></span>{/if}{row.action}
            </td>
          </tr>
        {/each}
      </tbody>
    </table>
  </section>

  <section aria-labelledby="waveform">
    <h2 id="waveform" class="label">07 Waveform</h2>
    <div class="mt-4 grid gap-4 sm:grid-cols-2">
      <figure class="border border-rule p-2">
        <Waveform peaks={[fakePeaks(7)]} category="kick" />
        <figcaption class="label mt-1">Mono · kick</figcaption>
      </figure>
      <figure class="border border-rule p-2">
        <Waveform peaks={[fakePeaks(11), fakePeaks(13)]} category="vocal" />
        <figcaption class="label mt-1">Stereo · vocal</figcaption>
      </figure>
    </div>
  </section>
</main>
