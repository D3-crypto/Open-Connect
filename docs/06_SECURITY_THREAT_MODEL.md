# OpenConnect - Security & Threat Model

## 1. Network Layer (DDoS & Rate Limiting)
**Threat:** A malicious actor attempts to overwhelm the VPS by opening millions of WebSockets or spamming the Razorpay API endpoints.
**Mitigations:**
- **Nginx Proxy Manager:** Configured to drop requests that exceed 50 req/sec per IP on the Django API endpoints.
- **Rust Relay Throttling:** The Rust server drops any WebSocket connection that attempts to send more than 10MB of binary data per second (unless specifically negotiating a file transfer).
- **Fail2Ban:** Bans IPs that repeatedly fail the cryptographic handshake or send malformed JSON payloads.

## 2. Application Layer (Injection Attacks)
**Threat:** SQL Injection via malicious device names, NoSQL/JSON injection in the payload, or Command Injection through the WireGuard wrapper.
**Mitigations:**
- **SQLi Protection:** Django's ORM completely abstracts raw SQL. All user inputs (like `device_name`) are parameterized and sanitized before hitting PostgreSQL.
- **Command Injection Protection:** The Python script that controls the WireGuard kernel (`wg set`) will **never** use `os.system()` with string formatting. It strictly uses `subprocess.run()` with array arguments to prevent `|| rm -rf /` style shell injections.
- **JSON Validation:** Incoming payloads are strictly validated against a Pydantic/Marshmallow schema before parsing.

## 3. Cryptographic Layer (Spoofing & Replay)
**Threat:** An attacker captures an encrypted clipboard payload over the Wi-Fi and tries to "replay" it later, or tries to forge a "Join Ecosystem" request.
**Mitigations:**
- **Replay Protection:** Every payload includes a monotonic timestamp and a nonce. If the receiver sees a nonce it has already processed, or a timestamp older than 60 seconds, the packet is instantly dropped.
- **Ed25519 Signatures:** The Razorpay Webhook and all "Join" requests require a cryptographic signature. If the signature math fails by even a single bit, the request is discarded.

## 4. Payment Layer (Bypass & Fraud)
**Threat:** Modified Android APKs ("Cracked Apps") that fake a successful Razorpay transaction.
**Mitigations:**
- The Android app's success token is entirely ignored for authorization.
- The Django Backend acts as the absolute source of truth. It relies **only** on server-to-server cryptographically signed webhooks from Razorpay (`razorpay_signature`).
- Rust WebSocket connects query the Django PostgreSQL state directly. If the DB says `status=FREE`, the Rust server physically refuses to route the packet to the global mesh.
