package com.example.ui_flutter.engine

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.Service
import android.content.Context
import android.content.Intent
import android.os.Build
import android.os.IBinder
import android.os.PowerManager
import android.util.Log
import android.app.PendingIntent
import android.content.ClipboardManager
import android.content.ClipData
import android.os.Handler
import android.os.Looper

class BackgroundMeshService : Service() {
    private val CHANNEL_ID = "OpenConnectMeshChannel"
    private val ACTION_RELOAD_ROSTER = "openconnect.RELOAD_ROSTER"
    private val ACTION_SEND_CLIPBOARD = "openconnect.SEND_CLIPBOARD"
    private val EXTRA_CLIPBOARD_TEXT = "clipboard_text"
    private var wakeLock: PowerManager.WakeLock? = null

    // Engine Components
    private lateinit var cryptoEngine: CryptoEngine
    private lateinit var rosterManager: RosterManager
    private lateinit var networkDiscovery: NetworkDiscovery
    private lateinit var meshClient: MeshClient
    private lateinit var meshServer: MeshServer
    private lateinit var bleRadar: BleRadar

    private var lastTrustedPeerIp: String? = null
    private var lastTrustedPeerPort: Int? = null

    private var clipboardManager: ClipboardManager? = null
    private var suppressNextClipboard = false
    private var lastLocalClipboard: String? = null
    private fun sendClipboardToPeer(text: String, source: String) {
        val peerIp = lastTrustedPeerIp
        val peerPort = lastTrustedPeerPort
        if (peerIp == null || peerPort == null) {
            Log.w("OpenConnect-Service", "Clipboard send skipped: no peer available ($source)")
            EventLog.add("Clipboard send skipped: no peer", "warning")
            networkDiscovery.startDiscovering()
            return
        }

        Log.i("OpenConnect-Service", "Sending clipboard ($source) to $peerIp:$peerPort")
        meshClient.sendClipboardWithRetry(text, peerIp, peerPort)
    }
    private val clipboardListener = ClipboardManager.OnPrimaryClipChangedListener {
        val manager = clipboardManager ?: return@OnPrimaryClipChangedListener
        val clip = manager.primaryClip
        val text = clip?.getItemAt(0)?.coerceToText(this)?.toString()?.trim().orEmpty()

        if (text.isEmpty()) return@OnPrimaryClipChangedListener
        if (suppressNextClipboard) {
            suppressNextClipboard = false
            return@OnPrimaryClipChangedListener
        }

        if (text == lastLocalClipboard) return@OnPrimaryClipChangedListener
        lastLocalClipboard = text
        EventLog.add("Clipboard copied", "info")
        sendClipboardToPeer(text, "auto")
    }

    override fun onCreate() {
        super.onCreate()
        Log.i("OpenConnect-Service", "Starting Foreground Mesh Service")
        createNotificationChannel()

        // Acquire Partial Wake Lock to prevent CPU sleep (but allow screen off)
        val powerManager = getSystemService(Context.POWER_SERVICE) as PowerManager
        wakeLock = powerManager.newWakeLock(PowerManager.PARTIAL_WAKE_LOCK, "OpenConnect::MeshWakeLock")
        wakeLock?.acquire()

        // Initialize Engines
        cryptoEngine = CryptoEngine(this)
        rosterManager = RosterManager(this)
        meshClient = MeshClient(this, cryptoEngine.getPublicKeyBase64()) { injectedText ->
            suppressNextClipboard = true
            lastLocalClipboard = injectedText
            EventLog.add("Clipboard received", "info")
        }
        
        meshServer = MeshServer(cryptoEngine.getPublicKeyBase64(), rosterManager, { injectedText ->
            Log.i("OpenConnect-Service", "📋 Injecting clipboard from mesh: [${injectedText.take(20)}...]")
            suppressNextClipboard = true
            lastLocalClipboard = injectedText
            EventLog.add("Clipboard received", "info")
            Handler(Looper.getMainLooper()).post {
                val clipboard = getSystemService(Context.CLIPBOARD_SERVICE) as ClipboardManager
                val clip = ClipData.newPlainText("OpenConnect", injectedText)
                clipboard.setPrimaryClip(clip)
            }
        }) { peerHost ->
            if (peerHost.isNotEmpty()) {
                lastTrustedPeerIp = peerHost
                lastTrustedPeerPort = 8765
            }
        }
        meshServer.startServer(8765)

        networkDiscovery = NetworkDiscovery(this, "Android_Device", cryptoEngine.getPublicKeyBase64()) { name, pubKey, ip, port ->
            if (rosterManager.isTrusted(pubKey)) {
                lastTrustedPeerIp = ip
                lastTrustedPeerPort = port
                meshClient.connectToPeer(ip, port)
            }
        }
        networkDiscovery.startBroadcasting(8765)
        networkDiscovery.startDiscovering()

        bleRadar = BleRadar(this, cryptoEngine.getPublicKeyBase64())
        bleRadar.startRadar()

        // Clipboard monitor for outbound sync
        clipboardManager = getSystemService(Context.CLIPBOARD_SERVICE) as ClipboardManager
        clipboardManager?.addPrimaryClipChangedListener(clipboardListener)
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        if (intent?.action == ACTION_RELOAD_ROSTER) {
            rosterManager.reloadRoster()
            Log.i("OpenConnect-Service", "🔁 Roster reloaded by request")
        }
        if (intent?.action == ACTION_SEND_CLIPBOARD) {
            val text = intent.getStringExtra(EXTRA_CLIPBOARD_TEXT)?.trim().orEmpty()
            if (text.isNotEmpty()) {
                suppressNextClipboard = true
                lastLocalClipboard = text
                sendClipboardToPeer(text, "manual")
                Log.i("OpenConnect-Service", "📤 Manual clipboard send triggered")
                EventLog.add("Manual clipboard send", "info")
            } else {
                Log.w("OpenConnect-Service", "Manual clipboard send skipped: empty text")
                EventLog.add("Manual clipboard send skipped", "warning")
            }
        }
        if (intent?.action == ACTION_SEND_CLIPBOARD && intent.hasExtra(EXTRA_CLIPBOARD_TEXT).not()) {
            val clipboard = getSystemService(Context.CLIPBOARD_SERVICE) as ClipboardManager
            val text = clipboard.primaryClip?.getItemAt(0)?.coerceToText(this)?.toString()?.trim().orEmpty()
            if (text.isNotEmpty()) {
                suppressNextClipboard = true
                lastLocalClipboard = text
                sendClipboardToPeer(text, "notification")
                Log.i("OpenConnect-Service", "📤 Notification clipboard send triggered")
                EventLog.add("Notification clipboard send", "info")
            } else {
                Log.w("OpenConnect-Service", "Notification clipboard send skipped: empty clipboard")
                EventLog.add("Notification clipboard send skipped", "warning")
            }
        }
        val notification: Notification = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val channel = NotificationChannel(
                CHANNEL_ID,
                "OpenConnect E2EE Mesh",
                NotificationManager.IMPORTANCE_LOW
            )
            val manager = getSystemService(NotificationManager::class.java)
            manager?.createNotificationChannel(channel)

            val sendClipboardIntent = Intent(this, BackgroundMeshService::class.java).apply {
                action = ACTION_SEND_CLIPBOARD
            }
            val sendClipboardPending = PendingIntent.getService(
                this,
                1001,
                sendClipboardIntent,
                PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
            )

            Notification.Builder(this, CHANNEL_ID)
                .setContentTitle("OpenConnect Mesh")
                .setContentText("E2EE Ecosystem is active offline and on Wi-Fi")
                .setSmallIcon(android.R.drawable.ic_dialog_info)
                .addAction(android.R.drawable.ic_menu_send, "Send clipboard", sendClipboardPending)
                .build()
        } else {
            @Suppress("DEPRECATION")
            val sendClipboardIntent = Intent(this, BackgroundMeshService::class.java).apply {
                action = ACTION_SEND_CLIPBOARD
            }
            val sendClipboardPending = PendingIntent.getService(
                this,
                1001,
                sendClipboardIntent,
                PendingIntent.FLAG_UPDATE_CURRENT
            )

            Notification.Builder(this)
                .setContentTitle("OpenConnect Mesh")
                .setContentText("E2EE Ecosystem is active offline and on Wi-Fi")
                .setSmallIcon(android.R.drawable.ic_dialog_info)
                .addAction(android.R.drawable.ic_menu_send, "Send clipboard", sendClipboardPending)
                .build()
        }

        // Elevate to Foreground Service to prevent Android from killing it
        startForeground(1, notification)
        return START_STICKY // Restart automatically if Android kills it due to low memory
    }

    override fun onDestroy() {
        Log.i("OpenConnect-Service", "Shutting down Mesh Service")
        meshServer.stopServer()
        meshClient.disconnect()
        bleRadar.stopRadar()
        clipboardManager?.removePrimaryClipChangedListener(clipboardListener)
        wakeLock?.release()
        super.onDestroy()
    }

    override fun onBind(intent: Intent?): IBinder? {
        return null
    }

    private fun createNotificationChannel() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val serviceChannel = NotificationChannel(
                CHANNEL_ID,
                "OpenConnect E2EE Mesh",
                NotificationManager.IMPORTANCE_LOW // Silent, no ringing
            )
            val manager = getSystemService(NotificationManager::class.java)
            manager?.createNotificationChannel(serviceChannel)
        }
    }
}
