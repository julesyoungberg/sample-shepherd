# Graph Report - sample-shepherd  (2026-11-13)

## Corpus Check
- 95 files · ~58,877 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 21 file(s) not represented in the graph (top: .patch 9, .toml 4, (none) 3)

## Summary
- 906 nodes · 1962 edges · 47 communities (34 shown, 13 thin omitted)
- Extraction: 94% EXTRACTED · 6% INFERRED · 0% AMBIGUOUS · INFERRED: 127 edges (avg confidence: 0.89)
- Token cost: 343,771 input · 0 output

## Community Hubs (Navigation)
- Legacy one-off scripts
- Plan and device listing
- Phase reports and library sources
- CLI commands
- Category baselines
- Library index
- Export render check
- Fourier overlay config
- Landing page dependencies
- Category evaluation
- JSON event stream
- Sync layer and config tests
- Config loading
- elektroid-cli output parsing
- CLI end-to-end tests
- Sync guard tests
- Device interface
- Desktop app plan
- Roadmap and landing page
- JSON event tests
- Elektron device backend
- Repo rules (CLAUDE.md)
- Organize layer and library tests
- User docs and config guide
- Test fixtures
- CLI reference generator
- Evaluation and upstream tools
- Landing page content
- Safety rules and device session
- Profile digitakt_2_50
- Profile digitakt_2_50_3
- Profile digitakt_2_50_4
- Profile generic_folder_3
- Profile generic_folder_4
- Fourier patches and profiles
- Legacy script tests
- Device listing walk
- Landing page layout
- graphify install hook
- Sync cancel and resume
- graphify Claude instructions
- Landing page prerender
- Favicon and brand palette
- Package root

## God Nodes (most connected - your core abstractions)
1. `build_parser()` - 30 edges
2. `run_sync()` - 25 edges
3. `Working notes: Digitakt II library build` - 25 edges
4. `_out()` - 23 edges
5. `make_wav()` - 21 edges
6. `BUDGETS` - 20 edges
7. `Device` - 20 edges
8. `ElektronDevice` - 20 edges
9. `Label` - 19 edges
10. `make_plan()` - 19 edges

## Surprising Connections (you probably didn't know these)
- `SAMPLE_SHEPHERD_LOCK_DIR per-device lock folder` --conceptually_related_to--> `device_lock()`  [INFERRED]
  docs/cli/configuration.md → src/sample_shepherd/util.py
- `Sync safety: per-device lock, --yes gate on rm/rmdir` --conceptually_related_to--> `device_lock()`  [INFERRED]
  docs/research-fourier-elektroid.md → src/sample_shepherd/util.py
- `_run()` --calls--> `main()`  [INFERRED]
  tests/test_eval.py → src/sample_shepherd/cli.py
- `Device interface (sample_shepherd.sync.device.Device)` --references--> `Device`  [EXTRACTED]
  docs/adding-a-device.md → src/sample_shepherd/sync/device.py
- `Adding a device family` --references--> `get_backend()`  [EXTRACTED]
  docs/adding-a-device.md → src/sample_shepherd/sync/device.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Sync safety guards (dry-run, --yes, project-use protection, device lock)** — claude_safety_invariants, readme_safety_first, docs_cli_commands_how_plan_decides, src_sample_shepherd_util_device_lock, docs_adding_a_device_empty_sample_list_rule [INFERRED 0.85]
- **CLI pieces the desktop app needs** — docs_cli_commands_json_output, docs_cli_commands_library_index, docs_cli_commands_plan_edit, docs_cli_commands_cooperative_stop, docs_desktop_app_plan_sidecar_protocol [EXTRACTED 1.00]
- **CLI user guides** — docs_cli_getting_started, docs_cli_configuration, docs_cli_commands, docs_cli_reference [EXTRACTED 1.00]
- **Fourier local patch series 0001-0009** — docs_history_phase1_report_sd_vendor_prefix_patch, docs_history_phase2b_plan_patch_0004_adaptive_folders, docs_history_phase2b_report_patch_0005_tempo_groups, docs_history_phase2b_report_patch_0006_foley_materials, docs_history_phase2c_plan_patch_0007_tonal_names, docs_history_phase2c_plan_patch_0008_finer_groups, docs_history_working_notes_digitakt_2_50_4_profile [INFERRED 0.85]
- **Library build phases 0 to 2c** — docs_history_phase0_report, docs_history_phase1_report, docs_history_phase2_report, docs_history_phase2b_plan, docs_history_phase2b_report, docs_history_phase2c_plan [EXTRACTED 1.00]
- **Device deletion safety guards** — docs_history_working_notes_matching_rule, docs_research_fourier_elektroid_used_samples_not_available, docs_research_fourier_elektroid_sync_safety_notes, scripts_delete_replaced, scripts_delete_list [INFERRED 0.75]

## Communities (47 total, 13 thin omitted)

### Community 0 - "Legacy one-off scripts"
Cohesion: 0.06
Nodes (38): main(), walk_render(), why_reasons(), main(), main(), ls(), main(), parse_size() (+30 more)

### Community 1 - "Plan and device listing"
Cohesion: 0.06
Nodes (41): cmd_plan(), cmd_plan_edit(), progress(), _emit_plan_rows(), collect(), Listed, load(), write() (+33 more)

### Community 2 - "Phase reports and library sources"
Cohesion: 0.05
Nodes (52): Phase 0 report: setup and inspection, CLAP model (laion/clap-htsat-unfused), Device path locks set at publish v1 / render --release, Fourier Samples (pinned 131ee62), Phase 1 test subset (480 files, 4 packs), Source library: Samples/sample packs (44,396 audio files), Samples/Sounds folder (undecided source), Phase 1 report: test run on 4 packs (+44 more)

### Community 3 - "CLI commands"
Cohesion: 0.08
Nodes (47): build_parser(), cmd_config_init(), cmd_config_show(), cmd_device_info(), cmd_device_listing(), cmd_device_ls(), cmd_eval_categories(), cmd_eval_import() (+39 more)

### Community 4 - "Category baselines"
Cohesion: 0.07
Nodes (24): folder(), _folder_category(), majority(), name(), named(), _parts(), rules(), _rx() (+16 more)

### Community 5 - "Library index"
Cohesion: 0.10
Nodes (19): category_of(), Changes, _check_paths(), _check_root(), _connect_ro(), index(), scan(), _walk() (+11 more)

### Community 6 - "Export render check"
Cohesion: 0.11
Nodes (14): check_render(), default_name_limit(), Issue, bundled_dir(), find(), list_profiles(), Profile, resolve() (+6 more)

### Community 7 - "Fourier overlay config"
Cohesion: 0.07
Nodes (27): advanced, BUDGETS, DIR_CAPS, FOLDER_ADAPTIVE, FOLDER_MIN_FILES, FOLDER_TARGET_FILES, MAX_PER_FAMILY, VENDOR_MAX_SHARE (+19 more)

### Community 8 - "Landing page dependencies"
Cohesion: 0.10
Nodes (25): @fontsource-variable/instrument-sans, svelte, @sveltejs/adapter-static, @sveltejs/kit, @sveltejs/vite-plugin-svelte, tailwindcss, @tailwindcss/vite, vite (+17 more)

### Community 9 - "Category evaluation"
Cohesion: 0.11
Nodes (18): manifest(), run(), _run(), test_baselines(), test_cli_eval_bundled_set_and_floor(), test_cli_eval_predictions_json_and_dry_run(), test_cli_import_ratings(), test_cli_sample_refuses_overwrite() (+10 more)

### Community 10 - "JSON event stream"
Cohesion: 0.09
Nodes (9): main(), Events, json_mode(), schema_path(), watch_for_stop(), _run(), test_missing_elektroid_is_a_clear_error(), _run() (+1 more)

### Community 11 - "Sync layer and config tests"
Cohesion: 0.12
Nodes (9): make_project(), test_bad_setting_inside_a_section_is_an_error(), test_parse_human_size(), test_unknown_setting_is_an_error(), test_entry_without_file_name(), test_missing_samples_list_is_an_error_not_empty(), test_not_a_zip(), test_read_manifest() (+1 more)

### Community 12 - "Config loading"
Cohesion: 0.16
Nodes (10): load_config(), _check_keys(), Config, example_config(), find_config_file(), _hint(), load(), _path() (+2 more)

### Community 13 - "elektroid-cli output parsing"
Cohesion: 0.14
Nodes (13): DeviceError, parse_info(), parse_ld(), parse_project_ls(), parse_sample_ls(), _subprocess_runner(), parse_human_size(), test_info_filesystems() (+5 more)

### Community 14 - "CLI end-to-end tests"
Cohesion: 0.19
Nodes (17): read_csv(), calls(), run(), test_config_init(), test_config_init_elsewhere_says_how_to_use_it(), test_config_init_notes_a_config_that_takes_precedence(), test_device_ls_and_info(), test_export_check_cli() (+9 more)

### Community 15 - "Sync guard tests"
Cohesion: 0.13
Nodes (6): FlakyDevice, MemoryDevice, RecordingDevice, test_a_stop_request_ends_the_sync_between_files_and_a_rerun_resumes(), test_hand_edited_deletes_are_rechecked(), test_ls_error_is_a_failure_not_a_missing_folder()

### Community 16 - "Device interface"
Cohesion: 0.14
Nodes (5): Device interface (sample_shepherd.sync.device.Device), Device, DeviceInfo, get_backend(), ProjectSlot

### Community 17 - "Desktop app plan"
Cohesion: 0.17
Nodes (14): Daily work log, Daily Project Work: Sample Shepherd task, Open questions for Jules (design, bundling Fourier, Developer ID, Windows, license, Node/Rust tooling), PR #16 Add library index, --json event stream (start/row/progress/result/error), library index command, plan-edit command, Desktop app plan (+6 more)

### Community 18 - "Roadmap and landing page"
Cohesion: 0.17
Nodes (13): Roadmap, Desktop app (desktop-app-plan.md), Landing page (site/, not deployed), TUI or web page for reviewing plans, Publish CLI to PyPI and choose a license, Landing page README, src/app.css design tokens (field manual direction), src/lib/content.js (all page words) (+5 more)

### Community 19 - "JSON event tests"
Cohesion: 0.19
Nodes (8): run_json(), test_errors_become_error_events(), test_human_output_goes_to_stderr(), test_plan_edit_excludes_rows_the_app_unticked(), test_plan_streams_each_row_and_totals(), test_sync_reports_progress_and_stops_between_files_when_asked(), test_tools_names_what_is_missing(), test_tools_reports_each_tool()

### Community 21 - "Repo rules (CLAUDE.md)"
Cohesion: 0.17
Nodes (3): CLAUDE.md repo rules, Adding a device family, App testing plan

### Community 22 - "Organize layer and library tests"
Cohesion: 0.26
Nodes (8): make_wav(), rows(), snapshot(), test_cli_library_index_dry_run_writes_nothing(), test_index_reads_the_master_and_updates_incrementally(), test_index_refuses_a_db_inside_the_master_or_another_masters_db(), test_index_skips_unreadable_files_and_indexes_the_rest(), render()

### Community 23 - "User docs and config guide"
Cohesion: 0.36
Nodes (12): Adding a device profile, Commands guide, Exit codes (0,1,2,3,130), Configuration guide, SAMPLE_SHEPHERD_LOCK_DIR per-device lock folder, Config file lookup order, Config settings table (work_dir, device, elektroid, fourier, export, sync protected, transfer), Getting started: sample packs to a synced Digitakt II (+4 more)

### Community 24 - "Test fixtures"
Cohesion: 0.20
Nodes (5): add_slot(), fake_device(), no_retry_sleep(), private_lock_dir(), world()

### Community 25 - "CLI reference generator"
Cohesion: 0.35
Nodes (6): _flag(), render(), _row(), _subcommands(), _table(), _walk()

### Community 26 - "Evaluation and upstream tools"
Cohesion: 0.20
Nodes (11): Packaging per OS and license collection, Evaluating category sorting, Baselines: majority, name, folder, rules, Growing a real test set (import-ratings, eval sample), Label provenance (folder-rule, documented, synthetic, listened, rated), Metrics: accuracy with bootstrap CI, coverage, acc|decided, macro-F1, Offering patches upstream, Elektroid elektroid-cli (GPLv3) (+3 more)

### Community 27 - "Landing page content"
Cohesion: 0.18
Nodes (9): changelog, credits, devices, docs, faq, features, pitch, REPO (+1 more)

### Community 28 - "Safety rules and device session"
Cohesion: 0.20
Nodes (7): Elektron Digitakt II, How plan decides (upload, delete candidates, keep-used, keep-protected), Organize -> export -> backup -> plan -> sync workflow, Device session 1 checklist, +Drive listing capture, scripts/ legacy one-off scripts, Supported devices table

### Community 29 - "Profile digitakt_2_50"
Cohesion: 0.25
Nodes (7): extends, status, value, id, name, paths, files_per_folder

### Community 30 - "Profile digitakt_2_50_3"
Cohesion: 0.25
Nodes (7): extends, status, value, id, name, paths, folder_depth

### Community 31 - "Profile digitakt_2_50_4"
Cohesion: 0.25
Nodes (7): extends, status, value, id, name, paths, folder_depth

### Community 32 - "Profile generic_folder_3"
Cohesion: 0.25
Nodes (7): extends, status, value, id, name, paths, folder_depth

### Community 33 - "Profile generic_folder_4"
Cohesion: 0.25
Nodes (7): extends, status, value, id, name, paths, folder_depth

### Community 35 - "Fourier patches and profiles"
Cohesion: 0.33
Nodes (7): Profile extends: chain and value/status fields, Our patches to Fourier Samples, Patch 0004 adaptive folders (FOLDER_ADAPTIVE, folder_depth 3), Patch 0009 section folders (CATEGORY_SECTIONS), Fourier patch series 0001-0009, Bundled device profiles (digitakt_2_50, _3, _4, generic_folder_3/_4), FOURIER_BASE

## Knowledge Gaps
- **37 isolated node(s):** `PATH`, `sample-shepherd`, `Claude graphify instructions (.claude/CLAUDE.md)`, `graphify skill trigger`, `Daily Project Work: Sample Shepherd task` (+32 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 305 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **13 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `device_lock()` connect `CLI commands` to `Legacy one-off scripts`, `Phase reports and library sources`, `Export render check`, `CLI end-to-end tests`, `Repo rules (CLAUDE.md)`, `User docs and config guide`?**
  _High betweenness centrality (0.098) - this node is a cross-community bridge._
- **Are the 23 inferred relationships involving `build_parser()` (e.g. with `cmd_config_init()` and `cmd_config_show()`) actually correct?**
  _`build_parser()` has 23 INFERRED edges - model-reasoned connections that need verification._
- **What connects `PATH`, `sample-shepherd`, `Claude graphify instructions (.claude/CLAUDE.md)` to the rest of the system?**
  _37 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Legacy one-off scripts` be split into smaller, more focused modules?**
  _Cohesion score 0.05605124685426676 - nodes in this community are weakly interconnected._
- **Why does `get_backend()` connect `Device interface` to `elektroid-cli output parsing`, `CLI commands`, `Elektron device backend`, `Repo rules (CLAUDE.md)`?**
  _High betweenness centrality (0.066) - this node is a cross-community bridge._
- **Should `Plan and device listing` be split into smaller, more focused modules?**
  _Cohesion score 0.05997778600518327 - nodes in this community are weakly interconnected._
- **Why does `Adding a device family` connect `Repo rules (CLAUDE.md)` to `Device interface`, `Evaluation and upstream tools`, `User docs and config guide`?**
  _High betweenness centrality (0.061) - this node is a cross-community bridge._