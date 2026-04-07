import os
from pathlib import Path
from dotenv import load_load_dotenv

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables from .env file
load_dotenv(os.path.join(BASE_DIR, '.env'))

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'fallback-insecure-key-for-dev')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv('DJANGO_DEBUG', 'True') == 'True'

ALLOWED_HOSTS = ['testserver', 'localhost', '127.0.0.1']

# OpenConnect Specific Settings
WG_SERVER_PUBLIC_KEY = os.getenv('WG_SERVER_PUBLIC_KEY', 'dev_server_pub_key')
WG_SERVER_ENDPOINT = os.getenv('WG_SERVER_ENDPOINT', 'vpn.local:51820')
RAZORPAY_KEY_ID = os.getenv('RAZORPAY_KEY_ID', '')
RAZORPAY_KEY_SECRET = os.getenv('RAZORPAY_KEY_SECRET', '')
RAZORPAY_WEBHOOK_SECRET = os.getenv('RAZORPAY_WEBHOOK_SECRET', '')

# Application definition
