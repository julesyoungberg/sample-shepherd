// Text for the landing page. Edit words here; the layout is in src/routes/+page.svelte.

export const REPO = 'https://github.com/julesyoungberg/sample-shepherd';

/** Link to a file in the repository on GitHub. tests/test_site_links.py checks it exists. */
export const repoFile = (path) => `${REPO}/blob/main/${path}`;

export const pitch =
  'Organize your sample library, export it for each instrument, and sync it to your sampler without breaking the projects already on it.';

export const features = [
  {
    title: 'Organize',
    body: 'Classify, name, dedupe, rate and folder thousands of samples. The sorting is done by Fourier Samples, which sample-shepherd runs for you.'
  },
  {
    title: 'Export per device',
    body: 'Render the same library for each target from a device profile: a Digitakt II layout, a plain folder for Ableton Live or XO, or a profile you write.'
  },
  {
    title: 'Sync safely',
    body: 'Back up the projects on your device, see which samples they use, and get a plan of what to upload and delete before anything changes.'
  },
  {
    title: 'Never lose a project sample',
    body: 'A sample any backed-up project uses is never deleted, matched by path or by content. With no project list at all, nothing is deleted.'
  },
  {
    title: 'Dry run first',
    body: 'Every command that writes has --dry-run. Nothing deletes without --yes. Uploads never overwrite, and deletes run only after every upload succeeds.'
  },
  {
    title: 'Resumable over slow links',
    body: 'Built for a 30,000-sample library over a USB link that moves about 77 KB/s. Stop a sync and run it again; it picks up where it left off.'
  }
];

export const screenshots = [
  { title: 'Library browser', caption: 'Browse and audition the whole library, colored by category.' },
  { title: 'Device map', caption: 'What fills the +Drive, and what is safe to clear.' },
  { title: 'Sync plan', caption: 'Every upload and delete, checked before it runs.' }
];

// Matches "Supported devices" in README.md.
export const devices = [
  { name: 'Digitakt II', sync: 'Yes, stereo kept', backup: 'Yes', tested: true },
  { name: 'Digitakt', sync: 'Yes, mono', backup: 'Yes' },
  { name: 'Analog Rytm MKI/MKII', sync: 'Yes, mono', backup: 'Yes' },
  { name: 'Model:Samples', sync: 'Yes, mono', backup: 'Yes' },
  { name: 'Syntakt', sync: 'No (slot-based samples only)', backup: 'Yes' },
  { name: 'Digitone I/II', sync: 'No sample storage', backup: 'Yes' }
];

export const docs = [
  { title: 'Getting started', path: 'docs/cli/getting-started.md', body: 'From sample packs to a synced Digitakt II, one step at a time.' },
  { title: 'Configuration', path: 'docs/cli/configuration.md', body: 'The config file, where it lives, and every setting.' },
  { title: 'Commands', path: 'docs/cli/commands.md', body: 'What each command reads and writes, and how it keeps your projects safe.' },
  { title: 'Adding a device profile', path: 'docs/adding-a-profile.md', body: 'Render for a sampler or layout we do not ship.' }
];

export const faq = [
  {
    q: 'Will it delete samples my projects use?',
    a: "No. It reads every backed-up project, and never deletes a sample one of them uses. An incomplete backup is refused, so a missing project can't make its samples look unused."
  },
  {
    q: 'Do I need the desktop app?',
    a: 'No. The command line tool does everything today. The app is being built on top of it and will run the same commands.'
  },
  {
    q: 'Which computers does it run on?',
    a: 'The command line tool needs Python 3.11 or newer and runs on macOS and Linux. The desktop app will start with macOS on Apple silicon.'
  },
  {
    q: 'Why do I install Elektroid separately?',
    a: 'Elektroid is GPLv3 software by its own authors. sample-shepherd runs its command line tool, elektroid-cli, as a separate program and does not include it.'
  },
  {
    q: 'Can I use it without a device?',
    a: 'Yes. Organizing and exporting work on files only, and so do checking an export and planning a sync from saved listings.'
  },
  {
    q: 'Is it free?',
    a: 'Yes. A donation link will be here for anyone who wants to support the work.'
  }
];

// Newest first. One line per release, in plain words.
export const changelog = [
  {
    version: '0.1.0',
    date: 'Unreleased',
    notes: [
      'One command, sample-shepherd, with organize, export and sync.',
      'Safe sync to Elektron devices: project backups, a delete plan that protects project samples, resumable uploads.',
      'Four-level folder layouts with section folders.',
      'A config file with checked settings, and guides for the command line.',
      'An evaluation of how well samples land in the right category.'
    ]
  }
];

export const credits = [
  {
    name: 'Fourier Samples',
    url: 'https://github.com/bvk7787/fourier-samples',
    license: 'Apache-2.0',
    note: 'Does the classifying and organizing. sample-shepherd runs it as a separate program, with our own patches.'
  },
  {
    name: 'Elektroid',
    url: 'https://github.com/dagargo/elektroid',
    license: 'GPLv3',
    note: 'Talks to Elektron devices. Installed separately; sample-shepherd runs elektroid-cli and does not include it.'
  },
  {
    name: 'Instrument Sans',
    url: 'https://github.com/Instrument/instrument-sans',
    license: 'OFL',
    note: 'The typeface on this page.'
  }
];
