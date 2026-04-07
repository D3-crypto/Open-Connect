# OpenConnect - Core Architecture

## Vision
OpenConnect is a zero-trust, end-to-end encrypted mesh ecosystem that seamlessly bridges Android, Linux, and Windows. It provides Apple-like Continuity features (clipboard sync, file streaming, universal control) without locking users into a proprietary cloud.

## The Freemium Model
- **Local Mode (Free & Open Source):** Devices use mDNS and Bluetooth LE to discover each other. Syncing works flawlessly peer-to-peer but is restricted to the local Wi-Fi network.
- **Global Relay Mode (Premium):** Devices connect to a central VPS via an auto-provisioned WireGuard tunnel. The VPS acts as a blind WebSockets relay, enabling global sync across different networks (e.g., 5G to Home Wi-Fi).

## Core Components

### 1. The Local Daemon (Linux/Windows)
A background service written in Python (`asyncio` + `websockets`).
- Handles local mDNS discovery.
- Manages local SQLite/JSON roster of trusted devices.
- Interfaces with OS APIs (wl-clipboard/xclip on Linux, win32clipboard on Windows).
- Automatically toggles between Local and Relay mode based on network availability.

### 2. The Android Client
A native Android application handling the mobile side of the mesh.
- Uses Android `VpnService` to programmatically build the WireGuard tunnel without QR codes.
- Interfaces with Android's Media and Notification APIs.
- For rooted devices (Optional): Injects call audio into `AudioFlinger` for VoIP handoff.

### 3. The VPS Relay Server (Django)
The backbone of the Premium tier. 
- **API Server:** Handles Razorpay subscription verification and dynamic WireGuard IP provisioning via `POST /api/vpn/register`.
- **WebSocket Relay:** Runs Rust or Django Channels with PostgreSQL Pub/Sub. Blindly routes encrypted binary payloads between devices based on their Public Keys. 
- **Zero-Knowledge:** The VPS never holds the private keys required to decrypt the payloads passing through it.

## The Cryptographic Identity System
OpenConnect does not use usernames or passwords to link devices. It uses a **Distributed Trust Roster**.
1. Every device generates a local Curve25519 Private/Public Keypair on installation.
2. The Public Key becomes the `Device_ID`.
3. Devices form an "Ecosystem" by exchanging and locally storing a `trusted_roster.json` containing the Public Keys and Capability Flags (e.g., `clipboard_in: true`) of their peers.
4. All payloads (files, clipboards) are encrypted symmetrically using AES-256, and the AES key is encrypted asymmetrically using the receiver's Public Key.
