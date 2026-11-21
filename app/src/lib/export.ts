// The Export screen's data: `export check --json` issues, and the run's counts.
import { parseEvents, type IssueRow } from './events';

// The `result` summary of `export check`.
export type CheckSummary = { files: number; folders: number; wav_checked: number; issues: number };

// The issues sorted by path (the CLI sends them in folder-walk order), and the result's
// summary, or null if the run didn't finish.
export function parseCheck(text: string): { issues: IssueRow[]; summary: CheckSummary | null } {
  const events = parseEvents(text);
  const issues = events
    .filter((e): e is IssueRow => e.type === 'row' && e.kind === 'issue')
    .sort((a, b) => (a.path < b.path ? -1 : a.path > b.path ? 1 : 0));
  const result = events.find((e) => e.type === 'result');
  return { issues, summary: (result?.summary as CheckSummary | undefined) ?? null };
}
