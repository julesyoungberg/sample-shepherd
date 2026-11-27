import { runCli } from '$lib/sidecar';
import recorded from '$lib/fixtures/library-ls.jsonl?raw';

export const load = () => runCli('library_ls', recorded);
