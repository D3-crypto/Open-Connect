# Intelligent Notification Handoff System

Standard apps like KDE Connect simply mirror *every single notification* from your phone to your laptop. This creates massive notification fatigue (e.g., getting pinged on your laptop because a random mobile game wants you to play, or seeing 15 WhatsApp messages stack up).

To achieve "Apple-Like" polish, OpenConnect will implement an **Intelligent Filter & Collapse** system.

## The One-Way Paradigm (Phone -> Desktop)
Through user research, we have established a core UX rule: **Notifications flow from Mobile devices to Desktop/Laptop devices, never the reverse.**
Laptops generally do not receive SMS, social media pings, or app alerts that a user would need to see on their phone while walking around. Therefore, we do not need to build complex Windows/Linux notification interceptors. Desktop devices only *display* incoming notifications from phones.

## 1. The Local Filtering Engine (On the Phone)
To save battery and network bandwidth, the filtering happens *before* the notification is ever encrypted or sent over the mesh.

### A. The "Do Not Disturb" (DND) Sync
*   If the Laptop is in "Focus Assist" or DND mode, it broadcasts a state change to the Phone. 
*   The Phone instantly stops sending non-critical notifications to the laptop.

### B. The Categorization Filter
Android 8.0+ uses Notification Channels. We will use these metadata tags to auto-filter:
1.  **Critical (Always Sync):** Phone Calls, SMS, Alarms, Calendar Reminders.
2.  **Messaging (Smart Sync):** WhatsApp, Telegram, Signal. 
    *   *Smart Collapse:* If you receive 5 WhatsApp messages from "Alice", KDE Connect sends 5 separate popups. OpenConnect will internally buffer them and send a single updated payload: `[WhatsApp: 5 New Messages from Alice]`.
3.  **Junk (Never Sync):** "Updates Available", "Game Energy Full", "Weather changes". The Android daemon will automatically drop these based on their Android `CATEGORY` flag (e.g., `CATEGORY_PROMO`).

## 2. Two-Way Dismissal (The Synchronization)
Apple Continuity allows you to clear a notification on your Mac, and it vanishes from your iPhone.

*   **How we build it:** When the Linux Daemon receives a notification, it stores the Android `Notification_ID`. If the user clicks "Dismiss" on the Kali Linux desktop notification, the Linux daemon sends a high-priority WebSocket packet: `{"type": "action", "action": "dismiss_notification", "id": 1234}`. 
*   The Android Kotlin daemon intercepts this, calls the `NotificationListenerService.cancelNotification()`, and the notification instantly disappears from the phone screen.

## 3. Actionable Handoffs
We won't just mirror text. We will mirror the *Quick Actions*.
*   If an SMS arrives with a "Reply" button, that button is sent to the Linux DBus notification.
*   When the user types a reply on their Kali laptop and hits Enter, the text is encrypted, sent over the mesh, and the Android daemon executes the Android `PendingIntent` to send the SMS invisibly from the phone.
