// The Library screen's data: samples from `library ls --json`, and the filters over them.

// Fourier's categories (the index's `category`) grouped onto the palette in categories.js.
const paletteOf = {
  KICKS: 'kick', SNARES: 'snare', CLAPS: 'snare', HATS: 'hat', CYMBALS: 'hat',
  TOMS: 'perc', PERC: 'perc', DRUMLOOPS: 'loop', PHRASES: 'loop', SUB: 'bass',
  SYNTH: 'tonal', STABS: 'tonal', PADS: 'tonal', PIANO: 'tonal', ACOUSTIC: 'tonal', WAVES: 'tonal',
  FX: 'fx', BLIPS: 'fx', VOX: 'vocal'
};

// The palette name for a sample's category, or null (no color) when it has none.
export const paletteFor = (category) => paletteOf[category] ?? null;

// Samples from the CLI's output: one JSON event per line, keeping the `sample` rows.
export function parseSamples(text) {
  return text
    .split('\n')
    .filter((line) => line.trim())
    .map((line) => JSON.parse(line))
    .filter((e) => e.type === 'row' && e.kind === 'sample');
}

// Every folder that holds samples or folders that do, with its sample count (including
// subfolders), sorted so each folder follows its parent.
export function folderTree(samples) {
  const counts = new Map();
  for (const s of samples) {
    const parts = s.folder ? s.folder.split('/') : [];
    for (let i = 1; i <= parts.length; i++) {
      const path = parts.slice(0, i).join('/');
      counts.set(path, (counts.get(path) ?? 0) + 1);
    }
  }
  // Compare with '/' as the lowest character, so "Drums Extra" can't land between "Drums" and "Drums/Kicks".
  const key = (path) => path.replaceAll('/', '\0');
  return [...counts]
    .sort(([a], [b]) => (key(a) < key(b) ? -1 : 1))
    .map(([path, count]) => ({ path, name: path.split('/').at(-1), depth: path.split('/').length - 1, count }));
}

// The terrain: the folder tree as an icicle, one band per depth. Each folder spans `x` to
// `x + w` (fractions of the whole library, by sample count) inside its parent's span, and
// has a `category` when all its samples share one.
export function icicle(samples) {
  const cats = new Map();
  for (const s of samples) {
    const parts = s.folder ? s.folder.split('/') : [];
    for (let i = 1; i <= parts.length; i++) {
      const path = parts.slice(0, i).join('/');
      if (!cats.has(path)) cats.set(path, new Set());
      cats.get(path).add(s.category);
    }
  }
  const next = new Map([['', 0]]); // where each parent's next child starts
  return folderTree(samples).map((f) => {
    const parent = f.path.split('/').slice(0, -1).join('/');
    const x = next.get(parent);
    const w = f.count / samples.length;
    next.set(parent, x + w);
    next.set(f.path, x);
    const [only, ...rest] = cats.get(f.path);
    return { ...f, x, w, category: rest.length ? null : only };
  });
}

// Samples that match every filter that's set. `folder` includes its subfolders; `text`
// matches the path, case-insensitively; `channels` is 'mono' or 'stereo'; `rating` is a
// verdict or 'unrated'.
export function filterSamples(samples, { text = '', folder = '', category = '', channels = '', rating = '' } = {}) {
  const needle = text.trim().toLowerCase();
  return samples.filter(
    (s) =>
      (!folder || s.folder === folder || s.folder.startsWith(folder + '/')) &&
      (!needle || s.path.toLowerCase().includes(needle)) &&
      (!category || s.category === category) &&
      (!channels || (channels === 'mono' ? s.channels === 1 : s.channels >= 2)) &&
      (!rating || (s.rating ?? 'unrated') === rating)
  );
}

export function formatSize(bytes) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 ** 2) return `${Math.round(bytes / 1024)} KB`;
  return `${(bytes / 1024 ** 2).toFixed(1)} MB`;
}
