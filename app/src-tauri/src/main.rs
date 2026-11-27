// Keeps a console window from opening next to the app in Windows release builds.
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use std::process::Command;

// shortcut: runs `sample-shepherd` from PATH; spawn the bundled PyInstaller sidecar by its resolved path once that build exists.
const CLI: &str = "sample-shepherd";

/// Runs one CLI command and returns its stdout, the `--json` event stream. A failed command
/// still returns its stream, since its `error` event says what went wrong. Only a run with
/// no stream at all (not found, or a crash before the first event) is an `Err`.
fn run(program: &str, args: &[&str]) -> Result<String, String> {
    let out = Command::new(program)
        .args(args)
        .output()
        .map_err(|e| format!("couldn't run {program}: {e}"))?;
    let stdout = String::from_utf8_lossy(&out.stdout).into_owned();
    if stdout.trim().is_empty() && !out.status.success() {
        let stderr = String::from_utf8_lossy(&out.stderr);
        return Err(format!("{program} failed ({}): {}", out.status, stderr.trim()));
    }
    Ok(stdout)
}

// Commands are named one by one, so the webview can only run read-only ones.
#[tauri::command]
async fn library_ls() -> Result<String, String> {
    tauri::async_runtime::spawn_blocking(|| run(CLI, &["--json", "library", "ls"]))
        .await
        .map_err(|e| e.to_string())?
}

fn main() {
    tauri::Builder::default()
        .invoke_handler(tauri::generate_handler![library_ls])
        .run(tauri::generate_context!())
        .expect("error while running the sample-shepherd app");
}

#[cfg(all(test, unix))]
mod tests {
    use super::run;

    #[test]
    fn a_failed_command_keeps_its_event_stream() {
        let out = run("sh", &["-c", "echo '{\"type\":\"error\"}'; exit 2"]).unwrap();
        assert_eq!(out, "{\"type\":\"error\"}\n");
    }

    #[test]
    fn a_crash_with_no_events_is_an_error_with_stderr() {
        let err = run("sh", &["-c", "echo boom >&2; exit 1"]).unwrap_err();
        assert!(err.contains("boom"), "{err}");
    }

    #[test]
    fn a_missing_program_is_an_error() {
        assert!(run("no-such-sample-shepherd", &[]).is_err());
    }
}
