package com.example.ui_flutter.engine

import android.util.Log
import io.ktor.server.application.*
import io.ktor.server.engine.*
import io.ktor.server.cio.*
import io.ktor.server.routing.*
import io.ktor.server.websocket.*
import io.ktor.websocket.*
import kotlinx.coroutines.*
import org.json.JSONObject

class MeshServer(
    private val myPublicKey: String,
    private val rosterManager: RosterManager,
    private val onClipboardReceived: ((String) -> Unit)? = null,
    private val onTrustedPeerConnected: ((String) -> Unit)? = null
) {
    private var server: ApplicationEngine? = null

    fun startServer(port: Int) {
        if (server != null) return

        CoroutineScope(Dispatchers.IO).launch {
            server = embeddedServer(CIO, port = port, host = "0.0.0.0") {
                install(WebSockets) {
                    pingPeriodMillis = 15_000
                    timeoutMillis = 20_000
                }

                routing {
                    webSocket("/mesh") {
                        Log.i("OpenConnect-MeshServer", "🤝 Incoming Connection from Peer!")
                        val remoteHost = call.request.headers["X-Forwarded-For"]
                            ?.split(",")
                            ?.firstOrNull()
                            ?.trim()
                            ?: call.request.local.remoteHost
                        EventLog.add("Mesh peer connected", "info")
                        
                        try {
                            for (frame in incoming) {
                                if (frame is Frame.Text) {
                                    val text = frame.readText()
                                    Log.i("OpenConnect-MeshServer", "📩 Received Data: $text")
                                    
                                    val json = JSONObject(text)
                                    val senderKey = json.optString("sender_key", "").trim()
                                    Log.i("OpenConnect-MeshServer", "Sender key prefix: ${senderKey.take(8)}")
                                    
                                    // SECURITY: ZERO TRUST VERIFICATION
                                    if (rosterManager.isTrusted(senderKey)) {
                                        val deviceName = rosterManager.trustedPeers[senderKey]
                                        Log.i("OpenConnect-MeshServer", "✅ Validated Trusted Device: $deviceName")
                                        if (remoteHost.isNotEmpty()) {
                                            onTrustedPeerConnected?.invoke(remoteHost)
                                        }
                                        
                                        // Acknowledge connection
                                        val reply = """{"type_":"pong","sender_key":"\$myPublicKey","payload":"{\"msg\":\"Android Server Accepted E2EE\"}"}"""
                                        send(Frame.Text(reply))
                                        
                                        if (json.optString("type_") == "clipboard") {
                                            try {
                                                val payload = JSONObject(json.getString("payload"))
                                                val clipText = payload.optString("text")
                                                if (clipText.isNotEmpty()) {
                                                    Log.i("OpenConnect-MeshServer", "📋 Clipboard received from peer: [${clipText.take(20)}...]")
                                                    EventLog.add("Clipboard received", "info")
                                                    onClipboardReceived?.invoke(clipText)
                                                }
                                            } catch (e: Exception) {
                                                Log.e("OpenConnect-MeshServer", "Clipboard payload parse failed: ${e.message}")
                                            }
                                        }
                                    } else {
                                        Log.e(
                                            "OpenConnect-MeshServer",
                                            "❌ REJECTED UNTRUSTED DEVICE: ${senderKey.take(8)}... roster=${rosterManager.trustedPeers.keys.joinToString { it.take(8) }}"
                                        )
                                        EventLog.add("Untrusted device rejected", "warning")
                                        close(CloseReason(CloseReason.Codes.VIOLATED_POLICY, "Untrusted Device"))
                                    }
                                }
                            }
                        } catch (e: Exception) {
                            Log.e("OpenConnect-MeshServer", "Peer connection dropped: ${e.message}")
                            EventLog.add("Mesh peer disconnected", "warning")
                        } finally {
                            Log.i("OpenConnect-MeshServer", "💔 WebSocket Closed")
                        }
                    }
                }
            }.start(wait = true)
            Log.i("OpenConnect-MeshServer", "🌐 Android Mesh Server listening on port \$port")
        }
    }

    fun stopServer() {
        server?.stop(1000, 5000)
        server = null
        Log.i("OpenConnect-MeshServer", "🛑 Android Mesh Server Stopped")
    }
}
