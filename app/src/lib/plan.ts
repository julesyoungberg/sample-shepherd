// The Plan screen's data: `plan --json` (or `plan-edit --json`) rows, the run's totals,
// and the two flows drawn above the row list.
import { parseEvents, type PlanRow } from './events';

type Action = PlanRow['action'];

// The `result` summary of `plan` and `plan-edit` (see plan.totals in the CLI).
export type PlanSummary = {
  upload: number;
  upload_bytes: number;
  folders: number;
  delete: number;
  delete_bytes: number;
  excluded: number;
  est_seconds: number;
};

// The rows in the CLI's order, and the result's summary, or null if the run didn't finish.
export function parsePlan(text: string): { rows: PlanRow[]; summary: PlanSummary | null } {
  const events = parseEvents(text);
  const rows = events.filter((e): e is PlanRow => e.type === 'row' && e.kind === 'plan');
  const result = events.find((e) => e.type === 'result');
  return { rows, summary: (result?.summary as PlanSummary | undefined) ?? null };
}

// Each flow lists the actions it shows, in drawing order. The export flows into the device
// (upload or already there); what's on the device flows to its fate.
export const FLOWS: { name: string; actions: Action[] }[] = [
  { name: 'Export to device', actions: ['upload', 'excluded-upload', 'skip-exists'] },
  { name: 'On the device', actions: ['delete', 'excluded-delete', 'keep-used', 'keep-protected'] }
];

// One action's band: `x` and `w` are fractions of the larger flow's bytes, so both flows
// share a scale and the cost of a sync reads as width.
export type Band = { action: Action; count: number; bytes: number; x: number; w: number };

export function flows(rows: PlanRow[]): { name: string; bands: Band[] }[] {
  const tally = new Map<Action, { count: number; bytes: number }>();
  for (const r of rows) {
    const t = tally.get(r.action) ?? { count: 0, bytes: 0 };
    tally.set(r.action, { count: t.count + 1, bytes: t.bytes + (r.size ?? 0) });
  }
  const bytesOf = (actions: Action[]) => actions.reduce((sum, a) => sum + (tally.get(a)?.bytes ?? 0), 0);
  const scale = Math.max(1, ...FLOWS.map((f) => bytesOf(f.actions)));
  return FLOWS.map(({ name, actions }) => {
    let x = 0;
    const bands = actions.flatMap((action) => {
      const t = tally.get(action);
      if (!t?.bytes) return []; // nothing to draw: a missing file has no size
      const band = { action, ...t, x, w: t.bytes / scale };
      x += band.w;
      return [band];
    });
    return { name, bands };
  });
}

// Matches the CLI's fmt_duration.
export function formatDuration(seconds: number): string {
  const s = Math.max(0, Math.round(seconds));
  if (s < 90) return `${s} s`;
  if (s < 90 * 60) return `${Math.round(s / 60)} min`;
  return `${(s / 3600).toFixed(1)} h`;
}
