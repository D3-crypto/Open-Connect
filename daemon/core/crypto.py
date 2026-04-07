import nacl.utils
from nacl.public import PrivateKey, PublicKey, Box
from nacl.encoding import Base64Encoder
import json
import base64

class CryptoEngine:
    def __init__(self, private_key_b64=None):
        """
        Initializes the Crypto Engine. If no private key is provided, it generates a new one.
        This keypair acts as both the device's IDENTITY and its ENCRYPTION method.
        """
        if private_key_b64:
            self.private_key = PrivateKey(private_key_b64, encoder=Base64Encoder)
        else:
            self.private_key = PrivateKey.generate()
            
        self.public_key = self.private_key.public_key

    def get_public_key_b64(self):
        """Returns the public key as a base64 string (This is your Device ID)"""
        return self.public_key.encode(encoder=Base64Encoder).decode('utf-8')

    def get_private_key_b64(self):
        """NEVER SHARE THIS. Stores the private key locally."""
        return self.private_key.encode(encoder=Base64Encoder).decode('utf-8')

    def encrypt_payload_for_peer(self, target_public_key_b64, payload_dict):
        """
        Encrypts a JSON dictionary payload specifically for a target device.
        Uses Curve25519, XSalsa20, and Poly1305 (via NaCl Box).
        Only the target device's Private Key can decrypt this.
        """
        # 1. Parse target's public key
        target_pub_key = PublicKey(target_public_key_b64, encoder=Base64Encoder)
        
        # 2. Create the E2EE Box using OUR private key and THEIR public key
        box = Box(self.private_key, target_pub_key)
        
        # 3. Convert payload to bytes
        message_bytes = json.dumps(payload_dict).encode('utf-8')
        
        # 4. Encrypt! (NaCl automatically generates a random nonce and prepends it)
        encrypted_bytes = box.encrypt(message_bytes)
        
        # 5. Return as base64 string so it can be sent over WebSockets or HTTP easily
        return base64.b64encode(encrypted_bytes).decode('utf-8')

    def decrypt_payload_from_peer(self, sender_public_key_b64, encrypted_b64_string):
        """
        Decrypts a payload that was encrypted FOR US by a peer.
        Throws an exception if the signature is invalid or it was tampered with.
        """
        # 1. Parse sender's public key
        sender_pub_key = PublicKey(sender_public_key_b64, encoder=Base64Encoder)
        
        # 2. Create the E2EE Box (Order matters! OUR private, THEIR public)
        box = Box(self.private_key, sender_pub_key)
        
        # 3. Decode base64 to raw bytes
        encrypted_bytes = base64.b64decode(encrypted_b64_string)
        
        # 4. Decrypt! (Validates signature and decrypts)
        try:
            decrypted_bytes = box.decrypt(encrypted_bytes)
            return json.loads(decrypted_bytes.decode('utf-8'))
        except Exception as e:
            print(f"SECURITY ALERT: Failed to decrypt payload! {str(e)}")
            return None

# --- DEMONSTRATION ---
if __name__ == "__main__":
    print("--- OpenConnect Local E2EE Security Test ---")
    
    # 1. Generate identities for two devices
    laptop = CryptoEngine()
    phone = CryptoEngine()
    
    print(f"Laptop Public Key: {laptop.get_public_key_b64()}")
    print(f"Phone Public Key:  {phone.get_public_key_b64()}")
    
    # 2. Laptop copies text to clipboard and wants to send it to the Phone
    clipboard_data = {
        "type": "clipboard",
        "content": "Secret password for my bank account!",
        "timestamp": 1709283400
    }
    
    print("\n[+] Laptop is encrypting clipboard data FOR the phone...")
    encrypted_payload = laptop.encrypt_payload_for_peer(phone.get_public_key_b64(), clipboard_data)
    
    print(f"    Raw Network Data (What a hacker on Wi-Fi sees):\n    {encrypted_payload[:60]}...[truncated]")
    
    # 3. Phone receives the raw network data and decrypts it
    print("\n[+] Phone is decrypting the data...")
    decrypted_data = phone.decrypt_payload_from_peer(laptop.get_public_key_b64(), encrypted_payload)
    
    print(f"    Decrypted Content: {decrypted_data['content']}")
