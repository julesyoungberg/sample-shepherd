<script>
  import { filterSamples, folderTree, formatSize, icicle, paletteFor, parseSamples } from '$lib/library.js';
  // shortcut: a recorded `library ls --json` run stands in for the CLI; load from the sidecar once the Tauri shell exists.
  import fixture from '$lib/fixtures/library-ls.jsonl?raw';

  // shortcut: renders at most this many rows; add TanStack Virtual (in the plan) when real libraries make this cap bite.
  const MAX_ROWS = 500;

  const samples = parseSamples(fixture);
  const folders = folderTree(samples);
  const terrain = icicle(samples);
  const terrainDepth = Math.max(0, ...terrain.map((f) => f.depth + 1));
  const categoryOptions = [...new Set(samples.map((s) => s.category).filter(Boolean))].sort();
  const ratingOptions = [...new Set(samples.map((s) => s.rating ?? 'unrated'))].sort();

  let filters = $state({ text: '', folder: '', category: '', channels: '', rating: '' });
  let shown = $derived(filterSamples(samples, filters));
</script>

<svelte:head><title>Library · sample-shepherd</title></svelte:head>

<div class="grid h-screen grid-cols-[14rem_1fr] grid-rows-[auto_1fr]">
  <header class="col-span-2 flex flex-wrap items-center gap-4 border-b border-rule px-6 py-3">
    <h1 class="text-lg font-semibold">Library</h1>
    <input class="field" type="search" placeholder="Filter by name or path" aria-label="Filter" bind:value={filters.text} />
    <select class="field" aria-label="Category" bind:value={filters.category}>
      <option value="">All categories</option>
      {#each categoryOptions as c}<option value={c}>{c}</option>{/each}
    </select>
    <select class="field" aria-label="Channels" bind:value={filters.channels}>
      <option value="">Mono and stereo</option><option value="mono">Mono</option><option value="stereo">Stereo</option>
    </select>
    <select class="field" aria-label="Rating" bind:value={filters.rating}>
      <option value="">Any rating</option>
      {#each ratingOptions as r}<option value={r}>{r}</option>{/each}
    </select>
    <p class="label ml-auto" aria-live="polite">{shown.length} of {samples.length} samples</p>
  </header>

  <nav class="overflow-auto border-r border-rule py-2 font-mono text-xs" aria-label="Folders">
    <ul>
      <li>
        <button class="w-full px-4 py-1 text-left hover:bg-panel" aria-pressed={filters.folder === ''}
          class:font-semibold={filters.folder === ''} onclick={() => (filters.folder = '')}>All folders</button>
      </li>
      {#each folders as f}
        <li>
          <button class="flex w-full justify-between py-1 pr-4 text-left hover:bg-panel" style:padding-left="{1 + f.depth}rem"
            aria-pressed={filters.folder === f.path} class:font-semibold={filters.folder === f.path}
            onclick={() => (filters.folder = f.path)}>
            <span>{f.name}</span><span class="text-ink-soft">{f.count}</span>
          </button>
        </li>
      {/each}
    </ul>
  </nav>

  <main class="overflow-auto px-6 py-2">
    <!-- The terrain: each folder's width is its share of the samples. Clicking one filters like the tree. -->
    <section class="relative mb-4 font-mono text-xs" style:height="{terrainDepth * 1.75}rem" aria-label="Terrain">
      {#each terrain as f (f.path)}
        <button class="absolute h-7 overflow-hidden border border-paper px-1 text-left whitespace-nowrap hover:brightness-110"
          style:left="{f.x * 100}%" style:width="{f.w * 100}%" style:top="{f.depth * 1.75}rem"
          style:background={paletteFor(f.category) ? `var(--color-cat-${paletteFor(f.category)})` : 'var(--color-panel)'}
          class:text-paper={paletteFor(f.category)} class:outline-2={filters.folder === f.path} class:outline-signal={filters.folder === f.path}
          aria-pressed={filters.folder === f.path} title="{f.path}: {f.count}"
          onclick={() => (filters.folder = filters.folder === f.path ? '' : f.path)}>{f.name}</button>
      {/each}
    </section>
    <table class="w-full border-collapse font-mono text-xs">
      <thead class="sticky top-0 bg-paper">
        <tr class="h-7 border-b border-ink text-left">
          <th class="label font-normal">Name</th><th class="label font-normal">Category</th>
          <th class="label text-right font-normal">Seconds</th><th class="label pl-4 font-normal">Channels</th>
          <th class="label font-normal">Rating</th><th class="label text-right font-normal">Size</th>
        </tr>
      </thead>
      <tbody>
        {#each shown.slice(0, MAX_ROWS) as s (s.path)}
          <tr class="h-7 border-b border-rule hover:bg-panel" title={s.path}>
            <td>{s.path.split('/').at(-1)}</td>
            <td>
              {#if paletteFor(s.category)}<span class="mr-2 inline-block h-2 w-2" style:background="var(--color-cat-{paletteFor(s.category)})"></span>{/if}{s.category ?? '-'}
            </td>
            <td class="text-right">{s.duration?.toFixed(2) ?? '-'}</td>
            <td class="pl-4">{s.channels === 1 ? 'mono' : s.channels >= 2 ? 'stereo' : '-'}</td>
            <td class:text-signal={s.rating === 'drop' || s.rating === 'misfiled'}>{s.rating ?? '-'}</td>
            <td class="text-right">{formatSize(s.size)}</td>
          </tr>
        {/each}
      </tbody>
    </table>
    {#if shown.length > MAX_ROWS}
      <p class="label mt-2">Showing the first {MAX_ROWS}. Filter to see the rest.</p>
    {:else if shown.length === 0}
      <p class="mt-4 text-sm">No samples match these filters.</p>
    {/if}
  </main>
</div>
