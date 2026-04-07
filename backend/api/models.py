from django.db import models
import uuid

class SubscriptionStatus(models.TextChoices):
    FREE = 'FREE', 'Free'
    TRIAL = 'TRIAL', 'Trial'
    PREMIUM = 'PREMIUM', 'Premium'
    CANCELLED = 'CANCELLED', 'Cancelled'

class DeviceType(models.TextChoices):
    ANDROID = 'ANDROID', 'Android'
    LINUX = 'LINUX', 'Linux'
    WINDOWS = 'WINDOWS', 'Windows'

class User(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(blank=True, null=True)
    razorpay_customer_id = models.CharField(max_length=255, blank=True, null=True)
    subscription_status = models.CharField(
        max_length=20,
        choices=SubscriptionStatus.choices,
        default=SubscriptionStatus.FREE
    )
    trial_ends_at = models.DateTimeField(null=True, blank=True)
    subscription_expiry = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.email or str(self.id)

class Ecosystem(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ecosystems')
    name = models.CharField(max_length=255, default="My Mesh")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.owner.id})"

class Device(models.Model):
    public_key = models.CharField(max_length=255, primary_key=True)
    ecosystem = models.ForeignKey(Ecosystem, on_delete=models.CASCADE, related_name='devices')
    name = models.CharField(max_length=255)
    device_type = models.CharField(max_length=20, choices=DeviceType.choices)
    wireguard_ip = models.GenericIPAddressField(null=True, blank=True, unique=True)
    is_banned = models.BooleanField(default=False)
    last_seen = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} [{self.wireguard_ip}]"
