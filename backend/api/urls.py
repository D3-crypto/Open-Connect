from django.urls import path
from .views import VPNRegisterView
from .webhooks import RazorpayWebhookView

urlpatterns = [
    path('webhooks/razorpay', RazorpayWebhookView.as_view(), name='razorpay_webhook'),
    path('vpn/register', VPNRegisterView.as_view(), name='vpn_register'),
]
