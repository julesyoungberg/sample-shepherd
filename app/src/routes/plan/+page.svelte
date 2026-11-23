<script lang="ts">
  import { formatSize } from '$lib/library';
  import { flows, formatDuration, parsePlan } from '$lib/plan';
  import type { PlanRow } from '$lib/events';
  // shortcut: a recorded `plan-edit --json` run stands in for the CLI; run it from the sidecar once the Tauri shell exists.
  import fixture from '$lib/fixtures/plan.jsonl?raw';

  const { rows, summary } = parsePlan(fixture);
  const drawn = flows(rows);

  let action: PlanRow['action'] | '' = $state('');
  let shown = $derived(action ? rows.filter((r) => r.action === action) : rows);

  // Uploads and deletes change the device, so they get the signal color; deletes also the hatch.
  const changes = (a: string) => a === 'upload' || a === 'delete';
</script>

<svelte:head><title>Plan · sample-shepherd</title></svelte:head>

<main class="mx-auto max-w-5xl px-6 py-4">
  <header class="flex flex-wrap items-baseline gap-4 border-b border-rule pb-3">
    <h1 class="text-lg font-semibold">Sync plan</h1>
    {#if summary}
      <p class="label ml-auto">
        upload {summary.upload} files ({formatSize(summary.upload_bytes)}) into {summary.folders} folders,
        delete {summary.delete} ({formatSize(summary.delete_bytes)}){#if summary.excluded}, {summary.excluded} excluded{/if}, about {formatDuration(summary.est_seconds)}
      </p>
    {/if}
  </header>

  {#if rows.length === 0}
    <p class="mt-4 text-sm">{summary ? 'Nothing to do: the device already matches the export.' : "The plan didn't finish, so there's nothing to show."}</p>
  {:else}
    <!-- The flow: each action's width is its bytes. Clicking one filters the rows. -->
    <section class="mt-4 space-y-2 font-mono text-xs" aria-label="Flow">
      {#each drawn as f (f.name)}
        <div role="group" aria-label={f.name}>
          <p class="label">{f.name}</p>
          <div class="relative h-7">
            {#each f.bands as b (b.action)}
              <button class="absolute h-7 overflow-hidden border border-paper px-1 text-left whitespace-nowrap hover:brightness-110"
                class:bg-signal={b.action === 'upload'} class:text-paper={b.action === 'upload'}
                class:hatch-delete={b.action === 'delete'} class:bg-panel={!changes(b.action)}
                class:outline-2={action === b.action} class:outline-signal={action === b.action}
                style:left="{b.x * 100}%" style:width="{b.w * 100}%"
                aria-pressed={action === b.action} title="{b.action}: {b.count} files, {formatSize(b.bytes)}"
                onclick={() => (action = action === b.action ? '' : b.action)}>{b.action} {b.count}</button>
            {/each}
          </div>
        </div>
      {/each}
    </section>

    <table class="mt-4 w-full border-collapse font-mono text-xs">
      <thead>
        <tr class="h-7 border-b border-ink text-left">
          <th class="label text-right font-normal">Id</th><th class="label pl-4 font-normal">Action</th>
          <th class="label font-normal">Device path</th><th class="label text-right font-normal">Size</th>
          <th class="label pl-4 font-normal">Why</th>
        </tr>
      </thead>
      <tbody>
        {#each shown as r (r.id)}
          <tr class="h-7 border-b border-rule hover:bg-panel" title={r.local_path || r.device_path}>
            <td class="text-right">{r.id}</td>
            <td class="pl-4" class:text-signal={changes(r.action)}>{r.action}</td>
            <td>{r.device_path}</td>
            <td class="text-right">{r.size === null ? '-' : formatSize(r.size)}</td>
            <td class="pl-4">{r.reason}</td>
          </tr>
        {/each}
      </tbody>
    </table>
  {/if}
</main>
