// The CLI's `--json` events: one JSON object per line of stdout. These types mirror
// src/sample_shepherd/events.schema.json; change both together.

type Event<T extends string> = { v: 1; type: T };

export type StartEvent = Event<'start'> & { cmd: string; dry_run: boolean };

export type ToolRow = Event<'row'> & {
  kind: 'tool';
  name: string;
  found: boolean;
  path: string | null;
  version: string | null;
  enables: string[];
};

export type PlanRow = Event<'row'> & {
  kind: 'plan';
  id: number;
  action: 'upload' | 'delete' | 'skip-exists' | 'keep-used' | 'keep-protected' | 'skip-missing' | 'excluded-upload' | 'excluded-delete';
  device_path: string;
  local_path: string;
  size: number | null;
  reason: string;
  hash: string;
};

// export check: one thing the device would refuse or hide.
export type IssueRow = Event<'row'> & { kind: 'issue'; path: string; problem: string };

// library ls: one indexed sample.
export type SampleRow = Event<'row'> & {
  kind: 'sample';
  path: string;
  folder: string;
  category: string | null;
  duration: number | null;
  sample_rate: number | null;
  channels: number | null;
  size: number;
  sha256: string;
  rating: string | null;
};

// device listing: one file in the device's sample storage.
export type ListingRow = Event<'row'> & { kind: 'listing'; path: string; size: number | null; hash: string };

// device info: one storage's capacity, in bytes (each rounded by the device).
export type StorageRow = Event<'row'> & { kind: 'storage'; name: string; size: number; used: number; free: number };

export type ProgressEvent = Event<'progress'> & { done: number; total: number; bytes: number; eta_s: number | null };
export type WarnEvent = Event<'warn'> & { msg: string };
// `summary` differs per command; each screen types the one it reads.
export type ResultEvent = Event<'result'> & { ok: boolean; exit: number; summary: Record<string, unknown> };
export type ErrorEvent = Event<'error'> & {
  code: 'user_error' | 'device_busy' | 'device_error' | 'stopped' | 'internal';
  msg: string;
  exit: number;
};

export type CliEvent =
  | StartEvent | ToolRow | PlanRow | IssueRow | SampleRow | ListingRow | StorageRow | ProgressEvent | WarnEvent | ResultEvent | ErrorEvent;

// shortcut: trusts each line to match the schema, as the CLI is our own program; validate here if the app ever reads output from elsewhere.
export function parseEvents(text: string): CliEvent[] {
  return text
    .split('\n')
    .filter((line) => line.trim())
    .map((line) => JSON.parse(line) as CliEvent);
}
