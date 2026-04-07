# Spatial Awareness: How Devices Know Where They Are

When moving a mouse off the edge of a screen, how does the system know *which* device is sitting to the left, and which is sitting to the right? 

Apple achieves this seamlessly because they have a massive hardware advantage (U1 Ultra-Wideband chips). Since we are building an open-source tool for standard hardware (standard laptops, standard phones), we have to use software tricks to achieve the same result.

We will use a combination of **Manual Virtual Layouts** and **Acoustic/Bluetooth Proximity Detection**.

## Phase 1: The Virtual Layout Map (The Reliable Way)
Just like Windows Multi-Monitor settings, the user must define the physical layout of their devices in the OpenConnect Flutter UI.
1. The user opens the OpenConnect dashboard on their PC.
2. They see a visual representation of their devices (e.g., "Ezio's Laptop" in the center).
3. They drag the icon for "Pixel 7" and drop it to the *right* side of the laptop icon.
4. This configuration is saved to the local `trusted_roster.json` file.
5. When the Rust daemon detects the mouse hitting the right edge of the laptop screen, it looks at the JSON map, sees the Pixel 7 is configured to be on the right, and instantly routes the input events to that specific IP address.

## Phase 2: RSSI Triangulation & Device Gyroscopes (The Software Alternative)
Since acoustic spatial detection is physically impossible on most hardware (speakers cannot reliably emit >18kHz, and most laptops/phones do not have spatially separated stereo microphones), we cannot use sound to find device placement.

Instead, if we ever implement automatic spatial awareness, it will rely on a combination of **Bluetooth RSSI (Signal Strength)** and **Inertial Measurement Units (IMUs)**:
1.  **RSSI Mapping:** The laptop and phone constantly measure the Bluetooth Low Energy (BLE) signal strength between them. This gives us a rough estimate of *distance* (e.g., "The phone is within 1 meter").
2.  **IMU (Gyroscope/Accelerometer) Correlation:** When the user physically picks up the phone from the left side of the desk and places it on the right side, the phone's gyroscope registers a specific motion arc. 
3.  **The Bump Sync:** A more reliable method (used by apps like Bump) is to have the user simply "bump" their phone against the left or right side of their laptop screen once. The laptop's accelerometer and the phone's accelerometer detect the exact same shock spike at the exact same millisecond. Based on the force vector, the software permanently registers the device to that side of the layout.

*Conclusion:* Until hardware like U1 (Ultra-Wideband) becomes universally standardized across Android and Windows, Phase 1 (Manual Layout) is the only method that guarantees a frustration-free user experience.
