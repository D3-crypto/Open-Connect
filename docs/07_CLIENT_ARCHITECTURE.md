# Client Architecture Strategy

## 1. The Multi-Platform Dilemma
Building separate native apps for Android (Kotlin), iOS (Swift), Windows (C#), and Linux (Python/Rust) takes an eternity to maintain. However, cross-platform UI frameworks (Flutter, React Native) often struggle with deep system-level background tasks.

## 2. Our Hybrid "Iceberg" Approach
For OpenConnect, we will use a hybrid approach that gives us the best of both worlds: Write the UI once, but write the core engine natively. 

### The Tip of the Iceberg (The UI): Flutter
**Why Flutter?**
- We can write one single, beautiful, unified UI codebase in Dart.
- This UI will compile perfectly to an Android App, an iOS App, a Windows `.exe`, and a Linux Flatpak.
- The UI's *only* job is displaying the "Trusted Roster," showing the QR code for pairing, and holding the "Upgrade to Premium" button.
- It will NOT handle the actual networking or clipboard monitoring.

### The Bottom of the Iceberg (The Engine): Rust (Core Core) & Native Plugins
**Why Rust for the Core Engine?**
- You correctly pointed out stability, memory management, and secure connections. 
- A Python daemon is great for prototyping, but it eats ~50MB of RAM just sitting idle. A Go daemon eats ~20MB. A Rust daemon eats **<3MB** of RAM.
- If we write the core `CryptoEngine`, `mDNS Discovery`, and `WebSocket logic` in Rust, we can compile it into a `.so` (Linux), `.dll` (Windows), and `.aar` (Android) library. 
- We can then just plug this single, insanely fast, mathematically secure Rust engine into the Flutter UI using MethodChannels/FFI.

### The Deep OS Hooks (The Adapters)
Even with Rust handling the network, reading the clipboard or routing a phone call is totally different on every OS.
- **Android:** We must write native Kotlin background services (using `ForegroundService`, `NotificationListenerService`, and `VpnService` from the WireGuard repo). Flutter will just talk to this Kotlin service.
- **Linux/Windows:** The Rust engine can directly call standard OS APIs (like X11/Wayland DBus or Win32) to read clipboards and intercept notifications.

## Summary of the Stack
1. **The Brain (Rust):** E2EE Cryptography, WebSockets, mDNS.
2. **The Muscle (Kotlin / Win32):** Grabbing clipboard data, hooking into Android OS events.
3. **The Face (Flutter):** The settings dashboard and device list.