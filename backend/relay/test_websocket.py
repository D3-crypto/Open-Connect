import asyncio
import websockets
import json

async def test_connection():
    uri = "ws://127.0.0.1:9000/ws/test_laptop_public_key_123"
    print(f"[*] Attempting to connect to Rust Relay at {uri}...")
    
    try:
        async with websockets.connect(uri) as websocket:
            print("[+] Successfully connected!")
            
            # Send a dummy message
            msg = "Hello from Python Test Script!"
            print(f"[*] Sending message: {msg}")
            await websocket.send(msg)
            
            # Wait a moment to see if it stays alive
            await asyncio.sleep(2)
            print("[+] Connection stayed alive. Closing.")
    except Exception as e:
        print(f"[-] Connection failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_connection())
