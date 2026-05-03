package com.example.ui_flutter.engine

import android.content.ClipboardManager
import android.content.ClipData
import android.content.Context
import android.os.Handler
import android.os.Looper
import android.util.Log
import io.ktor.client.*
import io.ktor.client.engine.okhttp.*
import io.ktor.client.plugins.websocket.*
import io.ktor.http.*
import io.ktor.websocket.*
import kotlinx.coroutines.*
import org.json.JSONObject

class MeshClient(
    private val context: Context,
    private val myPublicKey: String,
    private val onClipboardInjected: ((String) -> Unit)? = null
) {
    private val client = HttpClient(OkHttp) {
        install(WebSockets) {
            pingInterval = 15_000
        }
    }
    
    private val scope = CoroutineScope(Dispatchers.IO + SupervisorJob())
    private var session: DefaultClientWebSocketSession? = null
    @Volatile private var connecting = false

    fun connectToPeer(ip: String, port: Int) {
        if (session != null && session?.isActive == true) return
        if (connecting) return
        connecting = true

        scope.launch {
            try {
                Log.i("OpenConnect-Mesh", "Attempting WS connection to ws://$ip:$port/mesh")
                client.webSocket(method = HttpMethod.Get, host = ip, port = port, path = "/mesh") {
                    session = this
                    Log.i("OpenConnect-Mesh", "✅ WebSocket E2EE Tunnel Established with $ip:$port")
                    EventLog.add("Mesh connected", "info")
                    
                    val handshake = """{"type_":"ping","sender_key":"$myPublicKey","payload":"{\"msg\":\"Hello from Android\"}"}"""
                    send(Frame.Text(handshake))

                    for (message in incoming) {
                        when (message) {
                            is Frame.Text -> {
                                val text = message.readText()
                                Log.i("OpenConnect-Mesh", "📩 Received E2EE Data: $text")
                                
                                try {
                                    val json = JSONObject(text)
                                    if (json.optString("type_") == "clipboard") {
                                        val payload = JSONObject(json.getString("payload"))
                                        val clipText = payload.optString("text")
                                        if (clipText.isNotEmpty()) {
                                            Log.i("OpenConnect-Mesh", "📋 Injecting copied text into Android Clipboard: [${clipText.take(20)}...]")
                                            EventLog.add("Clipboard received", "info")
                                            
                                            // Must run on Main Thread for Clipboard interactions
                                            Handler(Looper.getMainLooper()).post {
                                                val clipboard = context.getSystemService(Context.CLIPBOARD_SERVICE) as ClipboardManager
                                                val clip = ClipData.newPlainText("OpenConnect", clipText)
                                                clipboard.setPrimaryClip(clip)
                                                onClipboardInjected?.invoke(clipText)
                                            }
                                        }
                                    }
                                } catch (e: Exception) {
                                    Log.e("OpenConnect-Mesh", "Failed to parse E2EE payload: ${e.message}")
                                }
                            }
                            else -> {}
                        }
                    }
                }
            } catch (e: Exception) {
                Log.e("OpenConnect-Mesh", "❌ WebSocket connection failed", e)
                EventLog.add("Mesh connection failed: ${e.message}", "error")
            } finally {
                session = null
                connecting = false
            }
        }
    }

    fun sendClipboardWithRetry(text: String, ip: String, port: Int) {
        scope.launch {
            if (session == null || session?.isActive != true) {
                connectToPeer(ip, port)
                val deadline = System.currentTimeMillis() + 3_000
                while (System.currentTimeMillis() < deadline) {
                    if (session?.isActive == true) break
                    delay(150)
                }
            }
            if (session?.isActive == true) {
                sendClipboard(text)
            } else {
                Log.w("OpenConnect-Mesh", "Clipboard send skipped: session did not become active")
                EventLog.add("Clipboard send skipped: session inactive", "warning")
            }
        }
    }

    fun sendClipboard(text: String) {
        val activeSession = session
        if (activeSession == null || !activeSession.isActive) {
            Log.w("OpenConnect-Mesh", "Clipboard send skipped: no active mesh session")
            EventLog.add("Clipboard send skipped: no session", "warning")
            return
        }

        val payload = JSONObject().apply {
            put("type_", "clipboard")
            put("sender_key", myPublicKey)
            put("payload", JSONObject().put("text", text).toString())
        }

        scope.launch {
            try {
                activeSession.send(Frame.Text(payload.toString()))
                Log.i("OpenConnect-Mesh", "📤 Sent clipboard payload to mesh")
                EventLog.add("Clipboard sent", "info")
            } catch (e: Exception) {
                Log.e("OpenConnect-Mesh", "Failed to send clipboard payload: ${e.message}")
                EventLog.add("Clipboard send failed", "error")
            }
        }
    }
    
    fun disconnect() {
        scope.launch {
            session?.close(CloseReason(CloseReason.Codes.NORMAL, "User disconnected"))
            session = null
            Log.i("OpenConnect-Mesh", "WebSocket Session Closed.")
        }
    }
}
