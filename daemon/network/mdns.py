import asyncio
from zeroconf import ServiceBrowser, ServiceInfo, Zeroconf
import socket
import json

class OpenConnectListener:
    def __init__(self, my_public_key):
        self.peers = {}
        self.my_public_key = my_public_key

    def remove_service(self, zeroconf, type, name):
        print(f"[-] Peer left local network: {name}")

    def add_service(self, zeroconf, type, name):
        info = zeroconf.get_service_info(type, name)
        if info:
            addresses = [socket.inet_ntoa(a) for a in info.addresses]
            port = info.port
            properties = {k.decode('utf-8'): v.decode('utf-8') if v else None for k, v in info.properties.items()}
            
            peer_pub_key = properties.get('public_key')
            
            # Don't add ourselves
            if peer_pub_key == self.my_public_key:
                return

            print(f"[+] Found OpenConnect Peer: {name} at {addresses[0]}:{port}")
            print(f"    Public Key: {peer_pub_key}")
            
            self.peers[peer_pub_key] = {
                "ip": addresses[0],
                "port": port,
                "name": properties.get('device_name')
            }

    def update_service(self, zeroconf, type, name):
        """Required by newer zeroconf versions, called when a service updates its properties."""
        pass

class LocalDiscovery:
    def __init__(self, my_public_key, my_device_name, my_port=8765):
        self.zeroconf = Zeroconf()
        self.service_type = "_openconnect._tcp.local."
        self.my_public_key = my_public_key
        self.my_device_name = my_device_name
        self.my_port = my_port

    def start_broadcasting(self):
        desc = {
            'public_key': self.my_public_key,
            'device_name': self.my_device_name,
            'version': '1.0'
        }
        
        # Get local IP (simplistic approach for demo)
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(('10.255.255.255', 1))
            local_ip = s.getsockname()[0]
        except Exception:
            local_ip = '127.0.0.1'
        finally:
            s.close()

        self.info = ServiceInfo(
            self.service_type,
            f"{self.my_device_name}.{self.service_type}",
            addresses=[socket.inet_aton(local_ip)],
            port=self.my_port,
            properties=desc,
            server=f"{self.my_device_name}.local."
        )

        print(f"[*] Broadcasting local presence as {self.my_device_name} ({local_ip})")
        self.zeroconf.register_service(self.info)

    def start_listening(self):
        self.listener = OpenConnectListener(self.my_public_key)
        self.browser = ServiceBrowser(self.zeroconf, self.service_type, self.listener)
        print("[*] Listening for local OpenConnect peers via mDNS...")

    def stop(self):
        self.zeroconf.unregister_service(self.info)
        self.zeroconf.close()

if __name__ == "__main__":
    import time
    # Test script
    discovery = LocalDiscovery("test_pub_key_123", "Ezio_Laptop")
    discovery.start_broadcasting()
    discovery.start_listening()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        discovery.stop()
