# OpenConnect - Repository Structure

The project is broken into 3 main monorepo domains:

## 1. /daemon (Python)
The cross-platform core engine that runs on Linux and Windows.
- `core/crypto.py`: Curve25519 key generation and payload encryption.
- `core/roster.py`: Validates and syncs `trusted_roster.json`.
- `network/mdns.py`: Local Wi-Fi discovery using zeroconf.
- `network/ws_client.py`: The persistent connection to the VPS Relay.
- `os_layers/linux_clip.py`: Interacts with Wayland/X11 clipboard.
- `os_layers/win_clip.py`: Interacts with Windows Win32 API.

## 2. /mobile (Kotlin/Flutter)
The Android client application.
- `VpnManager`: Interfaces with Android `VpnService` to dynamically build WireGuard profiles from JSON API responses.
- `CryptoEngine`: Android implementation of Libsodium for E2EE.
- `NotificationListener`: Captures and syncs Android notifications to the mesh.
- `AudioBridge` (Root Only): Hooks into `AudioFlinger` for call/media routing.

## 3. /vps-backend (Django)
The centralized Zero-Knowledge relay server.
- `api/views.py`: REST endpoints for Razorpay verification and VPN registration.
- `vpn/manager.py`: Python wrapper to execute `wg` kernel commands for assigning IPs.
- `relay/consumers.py`: Django Channels AsyncWebsocketConsumer. Reads the destination Public Key in the packet header and routes the binary frame to the correct active socket.
