use std::process::{Command, Child};
use std::sync::Mutex;
use std::time::Duration;
use std::thread;

struct BackendProcess(Mutex<Option<Child>>);

fn start_backend() -> Result<Child, Box<dyn std::error::Error>> {
    // Start Python backend
    let child = Command::new("python3")
        .arg("app.py")
        .spawn()?;

    // Wait for backend to be ready
    println!("Waiting for backend to start...");
    for i in 0..30 {
        thread::sleep(Duration::from_secs(1));
        if let Ok(_) = reqwest::blocking::get("http://localhost:8000") {
            println!("Backend is ready!");
            return Ok(child);
        }
        if i % 5 == 0 {
            println!("Still waiting for backend... ({}/30)", i);
        }
    }

    Err("Backend failed to start within 30 seconds".into())
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
  tauri::Builder::default()
    .setup(|app| {
      if cfg!(debug_assertions) {
        app.handle().plugin(
          tauri_plugin_log::Builder::default()
            .level(log::LevelFilter::Info)
            .build(),
        )?;
      }

      // Start Python backend process
      let backend = start_backend()
          .expect("Failed to start Python backend");

      // Store backend process for cleanup
      app.manage(BackendProcess(Mutex::new(Some(backend))));

      Ok(())
    })
    .on_window_event(|window, event| {
      if let tauri::WindowEvent::Destroyed = event {
        // Kill backend when window closes
        if let Some(backend_state) = window.state::<BackendProcess>().0.lock().ok() {
          if let Some(mut backend) = backend_state.as_ref() {
            let _ = backend.kill();
          }
        }
      }
    })
    .run(tauri::generate_context!())
    .expect("error while running tauri application");
}
