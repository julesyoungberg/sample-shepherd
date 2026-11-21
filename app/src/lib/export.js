// The Export screen's data: `export check --json` issues, and the run's counts.

// The issues sorted by path (the CLI sends them in folder-walk order), and the result's
// summary ({ files, folders, wav_checked, issues }), or null if the run didn't finish.
export function parseCheck(text) {
  const events = text
    .split('\n')
    .filter((line) => line.trim())
    .map((line) => JSON.parse(line));
  const issues = events
    .filter((e) => e.type === 'row' && e.kind === 'issue')
    .sort((a, b) => (a.path < b.path ? -1 : a.path > b.path ? 1 : 0));
  return { issues, summary: events.find((e) => e.type === 'result')?.summary ?? null };
}
