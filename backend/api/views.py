from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import DeviceRegistrationSerializer
from .models import User, Ecosystem, Device, SubscriptionStatus
from .wireguard_manager import get_next_available_ip, add_wireguard_peer
from django.conf import settings

# This would ideally come from env variables
SERVER_PUBLIC_KEY = getattr(settings, 'WG_SERVER_PUBLIC_KEY', 'server_public_key_placeholder')
SERVER_ENDPOINT = os.getenv('WG_SERVER_ENDPOINT', '127.0.0.1:51820')

class VPNRegisterView(APIView):
    def post(self, request):
        serializer = DeviceRegistrationSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        validated_data = serializer.validated_data
        
        # 1. Verify User and Subscription
        try:
            user = User.objects.get(id=validated_data['user_id'])
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

        if user.subscription_status not in [SubscriptionStatus.PREMIUM, SubscriptionStatus.TRIAL]:
            return Response(
                {"error": "Global Mesh requires an active Premium or Trial subscription."},
                status=status.HTTP_403_FORBIDDEN
            )

        # 2. Get or Create Ecosystem for the user
        ecosystem, _ = Ecosystem.objects.get_or_create(
            owner=user,
            defaults={"name": f"{user.email or 'User'}'s Mesh"}
        )

        # 3. Check if device already exists
        device = Device.objects.filter(public_key=validated_data['public_key']).first()
        
        if not device:
            # New device: Assign an IP and save to DB
            assigned_ip = get_next_available_ip()
            device = Device.objects.create(
                public_key=validated_data['public_key'],
                ecosystem=ecosystem,
                name=validated_data['name'],
                device_type=validated_data['device_type'],
                wireguard_ip=assigned_ip
            )
            
            # Execute WireGuard command on the server
            # NOTE: If we are running this on a dev machine without WG installed, 
            # add_wireguard_peer will fail but we won't crash the API response for now.
            add_wireguard_peer(device.public_key, device.wireguard_ip)
            
        elif not device.wireguard_ip:
            # Existing device but no IP (upgraded from Free to Premium)
            assigned_ip = get_next_available_ip()
            device.wireguard_ip = assigned_ip
            device.save()
            add_wireguard_peer(device.public_key, device.wireguard_ip)

        # 4. Return the WireGuard config for the Android app to inject
        return Response({
            "status": "success",
            "device_ip": device.wireguard_ip,
            "server_public_key": SERVER_PUBLIC_KEY,
            "server_endpoint": SERVER_ENDPOINT,
            "allowed_ips": "10.7.0.0/24", # Route all mesh traffic through the tunnel
        }, status=status.HTTP_200_OK)
