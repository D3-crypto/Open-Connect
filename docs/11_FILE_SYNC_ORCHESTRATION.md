# Syncthing File Orchestration Strategy

One of the core features of OpenConnect is file access (seeing your phone's files on your laptop and vice versa) and high-speed drag-and-drop, even *without* universal mouse control active.

To avoid reinventing the wheel, we use **Syncthing** as the underlying file transfer engine, but we hide it completely from the user.

## The Problem with Standard Syncthing
Normally, Syncthing requires users to:
1. Open a web GUI (localhost:8384).
2. Manually copy a 56-character Device ID.
3. Manually paste it into the other device.
4. Manually accept folder sharing requests.
This is exactly the terrible user experience we are trying to fix!

## The OpenConnect Orchestration Solution
Our background daemon (Rust/Python) acts as the "Puppet Master" for the Syncthing binary.

### 1. Headless Execution
We bundle the Syncthing binary inside our app. When OpenConnect starts, it launches Syncthing in the background with `-no-browser` and a dynamically generated API key.

### 2. Auto-Peering (Zero Config)
When the OpenConnect daemon discovers a trusted device (either via mDNS on Wi-Fi or via the Global WireGuard mesh):
1. It looks at the device's public key in the `trusted_roster.json`.
2. It translates our public key into a Syncthing Device ID.
3. It makes a silent HTTP `POST /rest/config/devices` request to the local Syncthing engine, forcibly adding the other device.
4. Syncthing instantly connects to the peer via our `10.7.0.x` WireGuard IP or the local `192.168.x.x` IP.

### 3. The "Drop Zone" & Virtual Drive
Instead of manually creating shared folders in Syncthing:
*   **The Drop Zone:** OpenConnect automatically creates a default `~/OpenConnect/DropZone` folder and configures Syncthing to auto-accept files dropped here. If you drag a file into this folder on your laptop, it appears on your phone instantly.
*   **The Virtual Drive (FUSE / SAF):** 
    *   *Linux/Windows:* We can mount the Android device's storage as a network drive using SSHFS/SFTP over the WireGuard tunnel, allowing you to browse your phone's files natively in Windows Explorer or Nautilus.
    *   *Android:* We use Android's Storage Access Framework (SAF) to securely expose specific folders to the Syncthing engine.