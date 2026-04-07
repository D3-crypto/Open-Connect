import asyncio
import time
import os
from core.crypto import CryptoEngine
from core.roster import RosterManager
from network.mdns import LocalDiscovery
from network.mesh_socket import LocalMeshServer, LocalMeshClient
from os_layers.clipboard_bridge import ClipboardMonitor

class OpenConnectDaemon:
    def __init__(self, device_name):
        self.device_name = device_name
        self.port = 8765
        
        # 1. Initialize core components
        print(f"[*] Booting OpenConnect Daemon: {self.device_name}")
        self.roster = RosterManager()
        
        # Load or generate identity
        if os.path.exists("identity.key"):
            with open("identity.key", "r") as f:
                self.crypto = CryptoEngine(private_key_b64=f.read().strip())
        else:
            self.crypto = CryptoEngine()
            with open("identity.key", "w") as f:
                f.write(self.crypto.get_private_key_b64())
                
        print(f"[*] My Public Key: {self.crypto.get_public_key_b64()}")
        
        # Ensure we are in our own roster so we don't reject ourselves (edge cases)
        if self.crypto.get_public_key_b64() not in self.roster.roster["peers"]:
             self.roster.roster["peers"][self.crypto.get_public_key_b64()] = {"name": self.device_name, "role": "admin"}
             self.roster.save_roster()

        # 2. Network & OS Bridges
        self.discovery = LocalDiscovery(self.crypto.get_public_key_b64(), self.device_name, self.port)
        self.server = LocalMeshServer("0.0.0.0", self.port, self.crypto, self.roster)
        self.client = LocalMeshClient(self.crypto)
        
        # Wire up the receive callback
        self.server.on_message_received = self.handle_incoming_mesh_message
        
        # 3. Setup Clipboard Monitor
        self.clipboard = ClipboardMonitor(self.handle_local_clipboard_copy)

    def handle_incoming_mesh_message(self, decrypted_data, sender_pub_key):
        """Called when a peer sends us something over the local Wi-Fi"""
        msg_type = decrypted_data.get("type")
        
        if msg_type == "clipboard":
            content = decrypted_data.get("content")
            print(f"\n[+] Received Clipboard from Mesh: {content[:30]}...")
            self.clipboard.set_clipboard(content)
            
        elif msg_type == "notification":
            print(f"\n[+] Received Notification: {decrypted_data.get('title')} - {decrypted_data.get('text')}")

    def handle_local_clipboard_copy(self, copied_text):
        """Called when the user hits Ctrl+C on this computer"""
        print(f"\n[*] User copied text. Broadcasting to trusted peers...")
        
        payload = {
            "type": "clipboard",
            "content": copied_text,
            "timestamp": int(time.time())
        }
        
        if not hasattr(self, 'loop') or not self.loop:
            print("Warning: Async loop not fully running yet. Could not blast clipboard.")
            return
            
        # Schedule the network blast in the asyncio event loop safely from another thread
        asyncio.run_coroutine_threadsafe(self.blast_to_peers(payload), self.loop)

    async def blast_to_peers(self, payload):
        """Finds all trusted peers on the local Wi-Fi and sends the encrypted data"""
        local_peers = self.discovery.listener.peers
        
        for peer_pub_key, peer_info in local_peers.items():
            if self.roster.is_peer_trusted(peer_pub_key):
                print(f"    -> Sending to {peer_info['name']} ({peer_info['ip']})")
                await self.client.send_payload(
                    peer_info['ip'], 
                    peer_info['port'], 
                    peer_pub_key, 
                    payload
                )

    async def run(self):
        # Store the running loop so background threads can use it safely
        self.loop = asyncio.get_running_loop()
        
        # Start background threads
        self.clipboard.start()
        self.discovery.start_broadcasting()
        self.discovery.start_listening()
        
        # Start the WebSocket server and block forever
        await self.server.start_server()

if __name__ == "__main__":
    daemon = OpenConnectDaemon("Ezio_Kali_Laptop")
    try:
        asyncio.run(daemon.run())
    except KeyboardInterrupt:
        print("\n[*] Shutting down daemon...")
        daemon.clipboard.stop()
        daemon.discovery.stop()
