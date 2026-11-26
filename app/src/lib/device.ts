// The Device screen's data: `device listing --json` rows drawn as the +Drive map, marked
// with what a sync plan would do to each file, and `device info --json` for its free space.
import { parseEvents, type ListingRow, type PlanRow, type StorageRow } from './events';

export type ListingSummary = { files: number; bytes: number };

export function parseListing(text: string): { rows: ListingRow[]; summary: ListingSummary | null } {
  const events = parseEvents(text);
  const rows = events.filter((e): e is ListingRow => e.type === 'row' && e.kind === 'listing');
  const result = events.find((e) => e.type === 'result');
  return { rows, summary: (result?.summary as ListingSummary | undefined) ?? null };
}

// The +Drive's capacity, or null when the device didn't report it.
export const parseDrive = (text: string): StorageRow | null =>
  parseEvents(text).find((e): e is StorageRow => e.type === 'row' && e.kind === 'storage' && e.name === '+Drive') ?? null;

// A project uses it (keep it), or the plan deletes it. Protected paths are kept but not
// marked: they're kept by rule, not because a project needs them.
export type Mark = 'used' | 'delete';

export function marksFrom(plan: PlanRow[]): Map<string, Mark> {
  const marks = new Map<string, Mark>();
  for (const r of plan) {
    if (r.action === 'keep-used') marks.set(r.device_path, 'used');
    if (r.action === 'delete') marks.set(r.device_path, 'delete');
  }
  return marks;
}

// One sample's cell: `x` and `w` are fractions of its folder's bar.
export type Cell = { path: string; size: number; x: number; w: number; mark: Mark | null };
// One top-level folder: `w` is its bytes as a fraction of the largest folder's, so bars compare.
export type FolderBar = { name: string; count: number; bytes: number; w: number; cells: Cell[] };

export function driveMap(rows: ListingRow[], marks: Map<string, Mark>): FolderBar[] {
  const groups = new Map<string, ListingRow[]>();
  for (const r of rows) {
    const name = r.path.split('/')[1] ?? '';
    groups.set(name, [...(groups.get(name) ?? []), r]);
  }
  const bars = [...groups].map(([name, files]) => {
    const bytes = files.reduce((sum, f) => sum + (f.size ?? 0), 0);
    let x = 0;
    const cells = files.map((f) => {
      const w = bytes ? (f.size ?? 0) / bytes : 0;
      const cell = { path: f.path, size: f.size ?? 0, x, w, mark: marks.get(f.path) ?? null };
      x += w;
      return cell;
    });
    return { name, count: files.length, bytes, w: 0, cells };
  });
  const largest = Math.max(1, ...bars.map((b) => b.bytes));
  for (const b of bars) b.w = b.bytes / largest;
  return bars;
}

// A top-level folder's category for the palette: "01_KICKS" names KICKS.
export const folderCategory = (name: string): string => name.replace(/^\d+_/, '').toUpperCase();
