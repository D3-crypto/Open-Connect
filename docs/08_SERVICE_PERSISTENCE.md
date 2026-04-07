# Service Persistence Strategy
To achieve Apple-like Continuity, OpenConnect cannot just be a "normal app" that the user opens and closes. It must run as a highly-privileged, silent background service that starts automatically when the operating system boots.

Just like Docker or Ollama, the core engine must be a **Daemon**.

## 1. Linux (systemd)
On Linux (Ubuntu, Debian, Arch, Kali), the Rust engine will be installed as a system-level or user-level `systemd` service.
- **Path:** `~/.config/systemd/user/openconnect.service` (User level is preferred so it can access the user's Wayland/X11 clipboard session).
- **Behavior:** `Restart=always` ensures that if the daemon crashes, Linux restarts it instantly. `WantedBy=default.target` ensures it starts silently the moment the user logs in.

## 2. Windows (Windows Services & Task Scheduler)
Windows is notoriously aggressive about sleeping background tasks to save battery.
- **Core Engine:** Will be registered using the `sc.exe create` command as a native Windows Service, or via a hidden Task Scheduler job triggered `On Logon`.
- **UI Decoupling:** The Flutter UI will just be a lightweight system tray icon that talks to the Rust service via a local named pipe. If the user clicks the "X" on the Flutter window, the UI dies, but the Rust daemon keeps syncing the clipboard silently.

## 3. Android (Foreground Services + Battery Exemption)
Android is the hardest environment because the OS actively hunts down and kills background apps to save battery (Doze mode).
- **The Service:** We must use a `ForegroundService` tied to a persistent, silent notification (e.g., "OpenConnect is running"). This tells Android that the app is actively doing something the user wants.
- **Battery Optimization:** During onboarding, the Flutter app *must* use `ACTION_REQUEST_IGNORE_BATTERY_OPTIMIZATIONS` to beg the user to remove OpenConnect from Android's power-saving restrictions. Without this, Android will kill our mDNS and WebSocket listeners after 15 minutes of the screen being off.
- **Firebase/Matrix Wakeups:** For the Global VPS mode, if the phone *does* fall asleep, the Django server will send a high-priority push notification (FCM) that instantly wakes the Android daemon up just in time to receive the clipboard sync from the laptop.
