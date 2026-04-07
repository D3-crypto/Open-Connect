import os
import django
import sys
import json
import uuid

# Setup Django environment
sys.path.append('/mnt/ezio/OpenConnect/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'vps_relay.settings')
django.setup()

from api.models import User, Ecosystem, Device, SubscriptionStatus
from rest_framework.test import APIClient

def test_vpn_registration():
    print("--- Starting VPN Registration Test ---\n")
    
    # 1. Setup Test Data in Database
    print("[1] Creating test user with PREMIUM subscription...")
    test_user = User.objects.create(
        email="test_user@example.com",
        subscription_status=SubscriptionStatus.PREMIUM
    )
    print(f"    Created User ID: {test_user.id}")
    
    # 2. Simulate the API Request (Android Phone)
    print("\n[2] Simulating Android App API Request...")
    client = APIClient()
    payload = {
        "public_key": "x8f9abc123def456publickey789placeholder",
        "name": "Sonu's Pixel 7",
        "device_type": "ANDROID",
        "user_id": str(test_user.id)
    }
    
    print(f"    Sending Payload: {json.dumps(payload, indent=2)}")
    response = client.post('/api/vpn/register', payload, format='json')
    
    # 3. Output the results
    print("\n[3] API Response Received:")
    print(f"    Status Code: {response.status_code}")
    print(f"    Response Body: {json.dumps(response.data, indent=2)}")
    
    # 4. Verify Database State
    print("\n[4] Verifying PostgreSQL Database State...")
    device = Device.objects.get(public_key="x8f9abc123def456publickey789placeholder")
    print(f"    Device Name: {device.name}")
    print(f"    Assigned IP: {device.wireguard_ip}")
    print(f"    Assigned Ecosystem: {device.ecosystem.name}")
    
    print("\n--- Test Completed Successfully! ---")

if __name__ == "__main__":
    test_vpn_registration()
