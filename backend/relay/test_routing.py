import asyncio
import websockets
import json

async def test_mesh_routing():
    uri_laptop = "ws://127.0.0.1:9000/ws/Laptop_Key_123"
    uri_phone = "ws://127.0.0.1:9000/ws/Phone_Key_456"
    
    print("[*] Connecting Phone and Laptop to the Rust Mesh...")
    
    # Connect both devices simultaneously
    async with websockets.connect(uri_phone) as phone_ws, \
               websockets.connect(uri_laptop) as laptop_ws:
               
        print("[+] Both devices connected successfully.")
        
        # Laptop creates an encrypted payload meant for the Phone
        envelope = {
            "sender_public_key": "Laptop_Key_123",
            "target_public_key": "Phone_Key_456",
            "encrypted_payload": "x8f9abc123def456_fake_encrypted_clipboard_data"
        }
        
        print(f"\n[Laptop] Sending encrypted payload to Phone via Mesh...")
        await laptop_ws.send(json.dumps(envelope))
        
        # Phone listens for the incoming routed message
        try:
            # Wait up to 2 seconds for a response
            response = await asyncio.wait_for(phone_ws.recv(), timeout=2.0)
            received_envelope = json.loads(response)
            
            print(f"[Phone] Received Envelope!")
            print(f"        From: {received_envelope['sender_public_key']}")
            print(f"        Payload: {received_envelope['encrypted_payload']}")
            print("\n✅ MESH ROUTING TEST PASSED!")
            
        except asyncio.TimeoutError:
            print("\n❌ [Phone] Did not receive the message in time.")

if __name__ == "__main__":
    asyncio.run(test_mesh_routing())
