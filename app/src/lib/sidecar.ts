import { parseEvents, type ErrorEvent } from './events';

// The Tauri shell's global API (`withGlobalTauri` in src-tauri/tauri.conf.json). Absent in a plain browser.
type Tauri = { core: { invoke<T>(cmd: string): Promise<T> } };

export type CliRun = { text: string; error: string | null };

// Runs one read-only CLI command through the shell (see src-tauri/src/main.rs) and returns
// its event stream. A plain browser (pnpm dev, Playwright) gets the recorded run instead.
// `error` is the CLI's own error event, or why the command couldn't run or finish.
export async function runCli(command: 'library_ls', recorded: string): Promise<CliRun> {
  const tauri = (globalThis as { __TAURI__?: Tauri }).__TAURI__;
  if (!tauri) return { text: recorded, error: null };
  try {
    const text = await tauri.core.invoke<string>(command);
    const events = parseEvents(text);
    const failed = events.find((e): e is ErrorEvent => e.type === 'error');
    if (failed) return { text, error: failed.msg };
    // The CLI ends every run with a result or error event, even on a bug; neither means it was killed.
    if (!events.some((e) => e.type === 'result')) return { text, error: 'sample-shepherd stopped before it finished' };
    return { text, error: null };
  } catch (e) {
    return { text: '', error: String(e) };
  }
}
