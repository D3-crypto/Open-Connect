# UI Architecture: The OpenConnect Dashboard (Flutter)

The UI must reflect the exact capabilities of our local-first, zero-knowledge architecture. It should not look like a generic sync app; it should feel like a hardware control panel.

## The Core Concept: The "Radar" Map

Instead of a boring list of devices, the main screen will feature a "Radar Map" (Virtual Layout Map) that visualizes the spatial relationship between the user's devices.

### Key Screens

1.  **The Home Radar (Main Dashboard)**
    *   **Visual:** A top-down radar view showing the current device in the center. Connected devices orbit around it.
    *   **Interaction:** 
        *   Drag a device icon left/right of the laptop icon to set its "Spatial Layout" (for future universal mouse control).
        *   Tap a device to view its connection status (`Local Wi-Fi` vs `WireGuard Relay`).
    *   **Data Binding:** Reads directly from `trusted_roster.json` and active mDNS `DiscoveryManager` callbacks.

2.  **The Roster / Pairing Flow (Adding a Device)**
    *   **Concept:** Because we use Zero-Knowledge E2EE, we don't rely on cloud accounts to pair devices. 
    *   **Flow:** 
        *   Device A generates a QR code containing its `public_key`.
        *   Device B scans the QR code, adding Device A to its `trusted_roster.json`.
        *   (Optional: A 6-digit numeric PIN exchange for devices without cameras, like two laptops).

3.  **Engine Status & Settings**
    *   **Visual:** A terminal-like status card showing the health of the background daemons.
    *   **Toggles:**
        *   `Enable Background Sync` (Starts/Stops the Kotlin/Rust background services).
        *   `Smart Notification Handoff` (Toggle Android Category filtering).
        *   `Global Relay Mode` (Enable WireGuard connection to VPS when off Wi-Fi).

## Flutter & Native Integration (The Bridge)

Flutter cannot run our core networking (mDNS, Libsodium, WebSockets) reliably in the background when the app is swiped away. 
Therefore, **Flutter is purely a "dumb terminal"** that talks to our native engines via `MethodChannels` (Android) and `ffi` / local sockets (Rust/Linux).

*   **Android:** Flutter -> `MethodChannel` -> Kotlin `SyncService`
*   **Linux/Windows:** Flutter -> local socket -> Rust `openconnect-daemon`