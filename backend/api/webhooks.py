import json
import hmac
import hashlib
import os
import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from .models import User, SubscriptionStatus
import razorpay

logger = logging.getLogger(__name__)

RAZORPAY_KEY_ID = os.getenv('RAZORPAY_KEY_ID', '')
RAZORPAY_KEY_SECRET = os.getenv('RAZORPAY_KEY_SECRET', '')
RAZORPAY_WEBHOOK_SECRET = os.getenv('RAZORPAY_WEBHOOK_SECRET', '')

client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET)) if RAZORPAY_KEY_ID else None

@method_decorator(csrf_exempt, name='dispatch')
class RazorpayWebhookView(APIView):
    """
    Listens for server-to-server webhook events from Razorpay.
    This acts as the absolute source of truth for payment status.
    """
    def post(self, request):
        webhook_body = request.body.decode('utf-8')
        webhook_signature = request.headers.get('X-Razorpay-Signature')

        if not webhook_signature:
            logger.warning("Razorpay Webhook missing signature.")
            return Response({"error": "Missing signature"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # 1. Cryptographically verify the webhook came from Razorpay
            if client:
                client.utility.verify_webhook_signature(
                    webhook_body, 
                    webhook_signature, 
                    RAZORPAY_WEBHOOK_SECRET
                )
            else:
                # If we are in dev mode and don't have keys, allow testing but log a warning.
                logger.warning("Running without Razorpay Keys. Skipping signature validation.")
        except razorpay.errors.SignatureVerificationError:
            logger.error("Razorpay Webhook signature verification failed! Possible spoofing attempt.")
            return Response({"error": "Invalid signature"}, status=status.HTTP_403_FORBIDDEN)

        # 2. Parse the payload
        try:
            event = json.loads(webhook_body)
            event_name = event.get('event')
            payload = event.get('payload', {})
            
            logger.info(f"Received Razorpay Webhook Event: {event_name}")

            # Example: subscription.charged (Payment was successful)
            if event_name == 'subscription.charged':
                sub_data = payload.get('subscription', {}).get('entity', {})
                customer_id = sub_data.get('customer_id')
                
                if customer_id:
                    user = User.objects.filter(razorpay_customer_id=customer_id).first()
                    if user:
                        logger.info(f"Upgrading user {user.id} to PREMIUM.")
                        user.subscription_status = SubscriptionStatus.PREMIUM
                        user.save()
                    else:
                        logger.warning(f"Customer {customer_id} paid, but not found in DB.")

            # Example: subscription.cancelled
            elif event_name == 'subscription.cancelled':
                sub_data = payload.get('subscription', {}).get('entity', {})
                customer_id = sub_data.get('customer_id')
                
                if customer_id:
                    user = User.objects.filter(razorpay_customer_id=customer_id).first()
                    if user:
                        logger.info(f"Downgrading user {user.id} to CANCELLED.")
                        user.subscription_status = SubscriptionStatus.CANCELLED
                        user.save()
                        
                        # Trigger the Postgres NOTIFY to tell the Rust Relay to drop their connections
                        from django.db import connection
                        with connection.cursor() as cursor:
                            # We need to drop all devices owned by this user's ecosystems
                            for ecosystem in user.ecosystems.all():
                                for device in ecosystem.devices.all():
                                    notify_payload = f"CANCELLED:{device.public_key}"
                                    cursor.execute(f"NOTIFY subscription_events, '{notify_payload}'")
                                    logger.info(f"Sent DB Kill Signal for Device: {device.public_key}")

            return Response({"status": "ok"}, status=status.HTTP_200_OK)
            
        except json.JSONDecodeError:
            return Response({"error": "Invalid JSON"}, status=status.HTTP_400_BAD_REQUEST)
