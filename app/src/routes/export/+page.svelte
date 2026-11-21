<script lang="ts">
  import { parseCheck } from '$lib/export';
  // shortcut: a recorded `export check --json` run stands in for the CLI; run it from the sidecar once the Tauri shell exists.
  import fixture from '$lib/fixtures/export-check.jsonl?raw';

  const { issues, summary } = parseCheck(fixture);
</script>

<svelte:head><title>Export · sample-shepherd</title></svelte:head>

<main class="mx-auto max-w-4xl px-6 py-4">
  <header class="flex flex-wrap items-baseline gap-4 border-b border-rule pb-3">
    <h1 class="text-lg font-semibold">Export check</h1>
    {#if summary}
      <p class="label ml-auto">{summary.files} files in {summary.folders} folders, {summary.issues} {summary.issues === 1 ? 'issue' : 'issues'}</p>
    {/if}
  </header>

  {#if !summary && issues.length === 0}
    <p class="mt-4 text-sm">The check didn't finish, so there's nothing to show.</p>
  {:else if issues.length === 0}
    <p class="mt-4 text-sm">No issues: the device will take this render as it is.</p>
  {:else}
    <table class="mt-2 w-full border-collapse font-mono text-xs">
      <thead>
        <tr class="h-7 border-b border-ink text-left">
          <th class="label font-normal">Path</th><th class="label font-normal">Problem</th>
        </tr>
      </thead>
      <tbody>
        {#each issues as i, n (n)}
          <tr class="h-7 border-b border-rule hover:bg-panel">
            <td class="pr-4">{i.path}</td><td class="text-signal">{i.problem}</td>
          </tr>
        {/each}
      </tbody>
    </table>
  {/if}
</main>
