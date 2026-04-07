# OpenConnect - User & Authentication Flows

## Flow 1: Creating a New Ecosystem
1. User installs OpenConnect on Device A (e.g., Linux Laptop).
2. Daemon generates `Device_A_PrivateKey` and `Device_A_PublicKey`.
3. Daemon creates an empty `trusted_roster.json` and adds its own Public Key with "Admin" capabilities.
4. The Ecosystem is now initialized. 

## Flow 2: Adding a New Device (Local Mode)
1. User installs OpenConnect on Device B (e.g., Android Phone).
2. Phone generates `Device_B_PrivateKey` and `Device_B_PublicKey`.
3. Phone scans the local network via mDNS and sees Device A broadcasting `OpenConnect_Beacon`.
4. Phone sends a "Join Request" payload containing its Public Key to Device A.
5. Device A displays a prompt: *"Pixel 7 wants to join your ecosystem. Approve?"*
6. User clicks **Approve** on Device A.
7. Device A signs Device B's Public Key, adds it to the `trusted_roster.json`, and sends the updated roster back to Device B.
8. They are now peered and can exchange encrypted clipboards.

## Flow 3: Upgrading to Premium & Managing Subscriptions (Global Relay)
1. **Free Trial:** User clicks "Try Premium" to activate a 7-day free trial. The API updates their status to `TRIAL` and provisions the VPN.
2. **Upgrade:** User clicks "Enable Global Sync" on their phone and pays via Razorpay.
3. **Validation:** VPS validates Razorpay payment verification payload and upgrades status to `PREMIUM`.
4. **Provisioning:** VPS runs background script to add `Device_PublicKey` to the server's WireGuard interface and assigns an IP (e.g., `10.7.0.5`).
5. **Connection:** VPS returns the endpoint, Server Public Key, and `10.7.0.5` IP. Android App uses `VpnService` to silently build and launch the WireGuard tunnel.
6. **Cancellation/Downgrade:** User clicks "Cancel Subscription". API updates status to `CANCELLED` (or waits until `subscription_expiry` is reached, then falls back to `FREE`). When status reverts to `FREE`, the server triggers a Postgres `NOTIFY` event, and the Rust relay instantly drops their remote WebSocket connections.

## Flow 4: Sending a File (Zero-Knowledge)
1. Phone selects a 5GB video and sends it to Laptop.
2. Phone generates a random, single-use symmetric AES key (`S_KEY`).
3. Phone encrypts `S_KEY` using the Laptop's Public Key -> `Encrypted_S_KEY`.
4. Phone streams the video in 1MB chunks, encrypting each chunk with `S_KEY`.
5. Phone pushes `Encrypted_S_KEY` and the encrypted chunks to the VPS WebSocket.
6. VPS looks at the destination header (`Laptop_PubKey`) and blindly forwards the packets.
7. Laptop receives packets, uses its Private Key to decrypt `Encrypted_S_KEY`, and uses `S_KEY` to decrypt the video chunks directly to the hard drive.
