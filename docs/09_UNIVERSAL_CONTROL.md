# Advanced Continuity: Universal Control & Drag-and-Drop

Apple's "Universal Control" (moving a mouse seamlessly from a Mac to an iPad and dragging files between them) is the holy grail of multi-device ecosystems. It feels like magic, but under the hood, it is just high-speed network routing of HID (Human Interface Device) events.

Here is how OpenConnect will achieve this across Linux, Windows, and Android.

## 1. Universal Control (Mouse & Keyboard Sharing)
**How it works:**
Instead of sending a file or a clipboard string, the "Host" computer captures the raw X/Y mouse coordinates and keystrokes, encrypts them, and blasts them to the "Target" device over the local WebSocket (at 60-120 frames per second).

**The Implementation:**
*   **Linux Host:** We will leverage open-source tools like `barrier` or `libevdev` to capture the raw mouse/keyboard events before they reach the desktop environment.
*   **Windows Host:** We will use a low-level Win32 `SetWindowsHookEx` (specifically `WH_MOUSE_LL` and `WH_KEYBOARD_LL`) to capture the input.
*   **The Network (Rust):** The Rust daemon packages these inputs into tiny, low-latency UDP-like binary packets and sends them over our encrypted WireGuard mesh or local Wi-Fi.
*   **Android Target (The iPad Alternative):** On an Android tablet, we will inject these events into the OS. 
    *   *Non-Rooted:* We can use Android's `AccessibilityService` API to simulate taps and swipes. 
    *   *Rooted:* We can directly write to `/dev/input/eventX` to simulate a physical hardware mouse, giving true pixel-perfect 120hz pointer control.

## 2. Cross-Device Drag and Drop (The "Portal" Trick)
Dragging a file from a Windows desktop and dropping it onto an Android tablet screen requires bridging the OS GUI with our background network.

**How we fake it to look like Apple:**
1.  **The Drag (Host):** When you click and drag a file to the edge of your monitor (where the Android screen "virtually" sits), our background daemon detects the cursor hitting the screen edge.
2.  **The Handoff:** The host OS temporarily "swallows" the file drop event. Our Rust daemon instantly looks up the file path of what you are dragging.
3.  **The Transport:** It triggers our headless `Syncthing` engine (or a direct WebRTC file stream) to start transferring the file in the background at maximum Wi-Fi speed.
4.  **The Drop (Target):** The moment your mouse cursor appears on the Android screen, the Android UI shows a ghost image of the file. When you release your finger/mouse, the Android daemon takes the incoming file stream and drops it into the target folder.

## Why Our Architecture Makes This Possible
If we had built this entirely in Python or Flutter, Universal Control would be impossible (the latency would be too high, and the mouse would stutter).
Because we are using **Rust for the core engine**, we can process input events in microseconds. And because we are using **WireGuard/Local WebSockets**, the data travels instantly without bouncing through a cloud server. 
