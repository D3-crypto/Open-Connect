# Client Development Strategy: Desktop First

When building a multi-device ecosystem, building the Desktop Client before the Mobile Client is significantly more efficient.

## Why Desktop First?

1.  **Testing Environment:** Developing the core network logic (mDNS, WebSockets, Cryptography) on Linux/Windows allows for instant testing, rapid compilation, and deep terminal output.
2.  **The Target Sink:** A multi-device ecosystem requires two endpoints to function. By building a stable Linux daemon first, the Android app will have a reliable "Target Sink" to connect to and test against when we build it. It is much harder to build an Android app when you have nothing to sync *to*.
3.  **No Battery/Sandbox Constraints:** Unlike Android (which actively kills background processes and requires complex Foreground Services), Linux allows our Rust daemon to run unhindered. We can perfect the pure logic before adapting it to survive Android's aggressive battery sandbox.

## The Desktop Client Architecture (Rust)

We will port the Python prototype into a high-performance Rust binary (`openconnect-daemon`).

### Core Crates (Libraries) to Use:
*   **Networking:** `tokio` (Async runtime) and `tokio-tungstenite` (WebSockets).
*   **Discovery:** `mdns-sd` (Multicast DNS for local network discovery).
*   **Cryptography:** `sodiumoxide` (Rust bindings for Libsodium/Curve25519, perfectly matching our Android `Tink` or Python `PyNaCl` engines).
*   **Clipboard Hooks:** 
    *   *Linux:* `zbus` (For silent GNOME Wayland DBus integration) or `x11-clipboard`.
    *   *Windows:* `clipboard-win`.

### Execution Flow:
1.  **Startup:** Read `identity.key` and `trusted_roster.json` from `~/.config/openconnect/`.
2.  **Broadcast:** Announce `_openconnect._tcp.local` on Port 8765.
3.  **Listen:** Spawn the local WebSocket server to accept incoming connections from the phone.
4.  **Monitor:** Hook into the OS clipboard and loop silently. When a copy occurs, blast it to all active, trusted WebSocket connections.