from rest_framework import serializers
from .models import Device, DeviceType

class DeviceRegistrationSerializer(serializers.Serializer):
    public_key = serializers.CharField(max_length=255)
    name = serializers.CharField(max_length=255)
    device_type = serializers.ChoiceField(choices=DeviceType.choices)
    user_id = serializers.UUIDField() # To link it to an existing user/ecosystem
