import asyncio
import websockets
import json
from core.crypto import CryptoEngine
from core.roster import RosterManager

class LocalMeshServer:
    def __init__(self, host, port, crypto_engine: CryptoEngine, roster: RosterManager):
        self.host = host
        self.port = port
        self.crypto = crypto_engine
        self.roster = roster
        self.active_clients = set()
        
        # Callback function for when we successfully decrypt a message
        self.on_message_received = None

    async def handle_client(self, websocket, path):
        """This runs every time a peer connects to our local port"""
        peer_ip = websocket.remote_address[0]
        print(f"[Mesh] Incoming connection from {peer_ip}")
        
        self.active_clients.add(websocket)
        try:
            async for message in websocket:
                # 1. Parse the outer envelope
                try:
                    envelope = json.loads(message)
                    sender_pub_key = envelope.get("sender_public_key")
                    encrypted_payload = envelope.get("encrypted_payload")
                except json.JSONDecodeError:
                    print("[Mesh] Received malformed JSON envelope. Dropping.")
                    continue

                # 2. Check the Trust Roster (The Bouncer)
                if not self.roster.is_peer_trusted(sender_pub_key):
                    print(f"[Mesh] SECURITY: Rejected payload from untrusted key: {sender_pub_key[:8]}...")
                    continue

                # 3. Decrypt the payload
                print(f"[Mesh] Decrypting payload from trusted peer {sender_pub_key[:8]}...")
                decrypted_data = self.crypto.decrypt_payload_from_peer(sender_pub_key, encrypted_payload)
                
                if decrypted_data and self.on_message_received:
                    self.on_message_received(decrypted_data, sender_pub_key)
                    
        except websockets.exceptions.ConnectionClosed:
            print(f"[Mesh] Peer {peer_ip} disconnected.")
        finally:
            self.active_clients.remove(websocket)

    async def start_server(self):
        server = await websockets.serve(self.handle_client, self.host, self.port)
        print(f"[Mesh] E2EE WebSocket Server listening on {self.host}:{self.port}")
        await server.wait_closed()

class LocalMeshClient:
    def __init__(self, crypto_engine: CryptoEngine):
        self.crypto = crypto_engine

    async def send_payload(self, target_ip, target_port, target_pub_key, payload_dict):
        """Connects to a peer, encrypts the data, and sends it"""
        uri = f"ws://{target_ip}:{target_port}"
        try:
            async with websockets.connect(uri) as websocket:
                # 1. Encrypt for the specific target
                encrypted_payload = self.crypto.encrypt_payload_for_peer(target_pub_key, payload_dict)
                
                # 2. Create the outer envelope
                envelope = {
                    "sender_public_key": self.crypto.get_public_key_b64(),
                    "encrypted_payload": encrypted_payload
                }
                
                # 3. Blast it over the wire
                await websocket.send(json.dumps(envelope))
                print(f"[Mesh] Successfully sent encrypted payload to {target_ip}")
        except Exception as e:
            print(f"[Mesh] Failed to send payload to {target_ip}: {e}")
