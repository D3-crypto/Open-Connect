# OpenConnect - Technology Stack

## 1. VPS Relay Server (The High-Speed Router)
**Language: Rust**
- **Why:** Absolute memory safety, zero-cost abstractions, and C-level performance. Rust guarantees no buffer overflows or memory leaks, making it the most mathematically secure choice for handling millions of raw, encrypted binary WebSocket packets from unknown clients.
- **Framework:** `tokio` (for async I/O) + `tungstenite` or `axum` (for WebSockets).
- **Role:** Pure network routing. Holds thousands of persistent WebSockets open, reads the `target_id` (Public Key) from the packet header, and blasts the encrypted binary chunk to the target socket in microseconds.

## 2. VPS Control API (The Brain)
**Language: Python (Django/FastAPI + PostgreSQL)**
- **Why:** Python is the king of business logic, database ORMs, and scripting.
- **Role:** Handles Razorpay webhooks, user database, and running the `wg` (WireGuard) kernel commands to provision IP addresses.
- **PostgreSQL Integration:** Instead of Redis, Django uses PostgreSQL's advanced features for caching and pub/sub. PostgreSQL's `LISTEN`/`NOTIFY` or Logical Replication (CDC) can act as the message bus to communicate with the Rust Relay, while features like `UNLOGGED` tables provide high-speed caching suitable for replacing Redis in our architecture. This simplifies our infrastructure to a single powerful database.

## 3. The Local Daemons (Linux/Windows)
**Language: Python (or Rust if performance dictates)**
- Python provides the easiest cross-platform bindings to both Windows (`win32`) and Linux Wayland/X11 APIs.

## 4. The Mobile Client
**Language: Kotlin (Native Android)**
- Required for deep OS-level integration (`VpnService`, `AudioFlinger`, Accessibility Services) which frameworks like React Native/Flutter struggle with.
