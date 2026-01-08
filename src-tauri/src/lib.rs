use std::process::{Command, Child};
use std::sync::Mutex;
use std::time::Duration;
use std::thread;
use tauri::Manager;

struct BackendProcess(Mutex<Option<Child>>);

fn start_backend(app_handle: &tauri::AppHandle) -> Result<Child, Box<dyn std::error::Error>> {
    // Try to get the resource directory
    let resource_dir = app_handle.path().resource_dir()?;

    // Try different possible locations for app.py
    let possible_paths = vec![
        resource_dir.join("app.py"),
        resource_dir.join("_up_").join("app.py"),
        std::env::current_dir()?.join("app.py"),
    ];

    println!("Resource dir: {:?}", resource_dir);

    let mut app_path = None;
    let mut work_dir = None;

    for path in possible_paths {
        println!("Trying: {:?}", path);
        if path.exists() {
            work_dir = path.parent().map(|p| p.to_path_buf());
            app_path = Some(path);
            break;
        }
    }

    let app_path = app_path.ok_or("app.py not found in any expected location")?;
    let work_dir = work_dir.ok_or("Failed to determine working directory")?;

    println!("Starting Python backend from: {:?}", app_path);
    println!("Working directory: {:?}", work_dir);

    // Try to use 'uv run' if available (handles dependencies automatically)
    // Otherwise fall back to system python3
    let use_uv = std::process::Command::new("which")
        .arg("uv")
        .output()
        .map(|o| o.status.success())
        .unwrap_or(false);

    let mut cmd = if use_uv {
        println!("Using 'uv run' to start backend with system packages");
        // Create a writable venv location in tmp with access to system packages (for ROS2)
        let tmp_venv = std::env::temp_dir().join("rosbag_manager_venv");
        println!("Using venv at: {:?}", tmp_venv);

        // Create venv with system-site-packages if it doesn't exist
        if !tmp_venv.exists() {
            println!("Creating venv with --system-site-packages");
            let _ = std::process::Command::new("uv")
                .arg("venv")
                .arg("--system-site-packages")
                .arg(&tmp_venv)
                .output();
        }

        let mut c = Command::new("uv");
        c.arg("run");
        c.arg("--python").arg("python3");
        c.arg(&app_path);
        c.env("UV_PROJECT_ENVIRONMENT", &tmp_venv);
        c
    } else {
        println!("Using system python3");
        let mut c = Command::new("python3");
        c.arg(&app_path);
        c
    };

    // Start Python backend
    // Unset PYTHONHOME to use system Python instead of AppImage's broken paths
    // Preserve ROS2 environment by keeping system PYTHONPATH
    let system_pythonpath = std::env::var("PYTHONPATH").unwrap_or_default();

    // Filter out AppImage paths but keep ROS2 paths
    let filtered_pythonpath: Vec<&str> = system_pythonpath
        .split(':')
        .filter(|p| !p.contains(".mount_") && (p.contains("ros") || p.contains("opt")))
        .collect();

    let ros_pythonpath = filtered_pythonpath.join(":");

    let child = cmd
        .current_dir(&work_dir)
        .env_remove("PYTHONHOME")
        .env("PYTHONPATH", ros_pythonpath)
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
      let backend = start_backend(&app.handle())
          .expect("Failed to start Python backend");

      // Store backend process for cleanup
      app.manage(BackendProcess(Mutex::new(Some(backend))));

      // Get the main window and navigate to localhost
      let window = app.get_webview_window("main").expect("Failed to get main window");
      window.eval("window.location.href = 'http://localhost:8000'")
          .expect("Failed to navigate to backend");

      Ok(())
    })
    .on_window_event(|window, event| {
      if let tauri::WindowEvent::Destroyed = event {
        // Kill backend when window closes
        if let Ok(mut backend_state) = window.state::<BackendProcess>().0.lock() {
          if let Some(ref mut backend) = *backend_state {
            let _: Result<(), std::io::Error> = backend.kill();
          }
        }
      }
    })
    .run(tauri::generate_context!())
    .expect("error while running tauri application");
}
