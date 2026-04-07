# OpenConnect - PostgreSQL Database Schema

## Core Tables (Persistent / Logged)
These tables handle billing, identity, and access control.

### 1. `users` (Account Level)
- `id`: UUID (Primary Key)
- `email`: String (Optional, for receipts/recovery)
- `razorpay_customer_id`: String
- `subscription_status`: Enum (`FREE`, `TRIAL`, `PREMIUM`, `CANCELLED`)
- `trial_ends_at`: Timestamp (Null if trial used/not applicable)
- `subscription_expiry`: Timestamp
- `created_at`: Timestamp

### 2. `ecosystems` (The Mesh Networks)
- `id`: UUID (Primary Key)
- `owner_id`: UUID (Foreign Key -> `users.id`)
- `name`: String (e.g., "Personal Mesh", "Office Mesh")
- `created_at`: Timestamp

### 3. `devices` (The Cryptographic Identities)
- `public_key`: String (Primary Key, base64 encoded Curve25519)
- `ecosystem_id`: UUID (Foreign Key -> `ecosystems.id`)
- `name`: String (e.g., "Pixel 7", "Kali Laptop")
- `device_type`: Enum (`ANDROID`, `LINUX`, `WINDOWS`)
- `wireguard_ip`: String (e.g., "10.7.0.5" - Assigned by API)
- `is_banned`: Boolean (Default: False)
- `last_seen`: Timestamp

---

## Ephemeral Tables (UNLOGGED)
These tables act as our "Redis replacement". They live entirely in RAM/Memory and are wiped if the database restarts.

### 4. `active_connections` (UNLOGGED)
Used by Rust and Django to know who is currently online.
- `public_key`: String (Primary Key -> `devices.public_key`)
- `relay_node_id`: String (If scaling to multiple VPS relays later)
- `connected_at`: Timestamp
- `client_ip`: String (Their actual public IP)

### 5. `offline_queue` (UNLOGGED)
Holds encrypted payloads (like clipboard text) when a target device is asleep.
- `id`: BigInt (Auto-increment)
- `target_public_key`: String (Index)
- `sender_public_key`: String
- `encrypted_payload`: ByteA (Raw binary blob)
- `expires_at`: Timestamp (Auto-deletes after 24 hours)

---

## Postgres LISTEN/NOTIFY Channels
Instead of Redis Pub/Sub, the Rust Relay listens to these PostgreSQL channels:

1. **`channel_auth_events`**
   - Payload: `{"action": "disconnect", "public_key": "x8f9..."}`
   - Triggered by Django when a Razorpay sub expires or a device is banned.
   - Action: Rust instantly drops the WebSocket connection.

2. **`channel_queue_events`**
   - Payload: `{"action": "flush_queue", "target": "x8f9..."}`
   - Triggered when a device comes online.
   - Action: Rust queries the `offline_queue` table and blasts the pending packets to the newly connected device.
