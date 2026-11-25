<script lang="ts">
  import { formatSize, paletteFor } from '$lib/library';
  import { driveMap, folderCategory, marksFrom, parseDrive, parseListing } from '$lib/device';
  import { parsePlan } from '$lib/plan';
  // shortcut: recorded `device listing --json`, `device info --json` and `plan-edit --json` runs stand in for the CLI; run them from the sidecar once the Tauri shell exists.
  import listingFixture from '$lib/fixtures/device-listing.jsonl?raw';
  import infoFixture from '$lib/fixtures/device-info.jsonl?raw';
  import planFixture from '$lib/fixtures/plan.jsonl?raw';

  const { rows, summary } = parseListing(listingFixture);
  // shortcut: one positioned element per sample; move to canvas (as the plan says) once a full drive's 10,000+ cells feel slow.
  const bars = driveMap(rows, marksFrom(parsePlan(planFixture).rows));
  const drive = parseDrive(infoFixture);
  const color = (name: string) => {
    const p = paletteFor(folderCategory(name));
    return p ? `var(--color-cat-${p})` : 'var(--color-ink-soft)';
  };
</script>

<svelte:head><title>Device · sample-shepherd</title></svelte:head>

<main class="mx-auto max-w-5xl px-6 py-4">
  <header class="flex flex-wrap items-baseline gap-4 border-b border-rule pb-3">
    <h1 class="text-lg font-semibold">+Drive</h1>
    {#if summary}<p class="label ml-auto">{summary.files} files, {formatSize(summary.bytes)}</p>{/if}
    {#if drive}<p class="label">{formatSize(drive.used)} used of {formatSize(drive.size)}, {formatSize(drive.free)} free</p>{/if}
  </header>

  {#if drive && rows.length}
    <!-- The whole drive: each folder's share, then free space as empty paper. -->
    <div class="mt-3 flex h-3 border border-rule" role="img" aria-label="+Drive space: {formatSize(drive.free)} free">
      {#each bars as b (b.name)}
        <div class="border-r border-paper" style:width="{(b.bytes / drive.size) * 100}%" style:background={color(b.name)}
          title="{b.name}: {formatSize(b.bytes)}" data-folder={b.name}></div>
      {/each}
    </div>
  {/if}

  {#if rows.length === 0}
    <p class="mt-4 text-sm">{summary ? 'The +Drive is empty.' : "The listing didn't finish, so there's nothing to show."}</p>
  {:else}
    <p class="mt-3 text-xs">
      One cell per sample, its width its bytes. <span class="ml-2 inline-block h-3 w-3 align-middle outline-2 outline-ink"></span> a project uses it;
      <span class="ml-2 hatch-delete inline-block h-3 w-3 align-middle"></span> the plan deletes it.
    </p>
    <section class="mt-3 space-y-2 font-mono text-xs" aria-label="+Drive map">
      {#each bars as b (b.name)}
        <div role="group" aria-label={b.name} class="grid grid-cols-[10rem_1fr] items-center gap-3">
          <p title="{b.count} files, {formatSize(b.bytes)}">{b.name} <span class="text-ink-soft">{formatSize(b.bytes)}</span></p>
          <div class="relative h-7" style:width="{b.w * 100}%" data-bar>
            {#each b.cells as c (c.path)}
              <div class="absolute h-7 border border-paper"
                class:outline-2={c.mark === 'used'} class:outline-ink={c.mark === 'used'} class:-outline-offset-2={c.mark === 'used'}
                style:left="{c.x * 100}%" style:width="{c.w * 100}%" style:background={color(b.name)}
                role="img" aria-label="{c.path}, {formatSize(c.size)}{c.mark === 'used' ? ', used by a project' : c.mark === 'delete' ? ', the plan deletes it' : ''}"
                title="{c.path}: {formatSize(c.size)}">
                {#if c.mark === 'delete'}<div class="hatch-delete absolute inset-0"></div>{/if}
              </div>
            {/each}
          </div>
        </div>
      {/each}
    </section>
  {/if}
</main>
