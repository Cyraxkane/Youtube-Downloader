import os
from datetime import timedelta

# Base directory of the application
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# Download directory
DOWNLOAD_DIR = os.path.join(BASE_DIR, 'downloads')
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# Logs directory
LOGS_DIR = os.path.join(BASE_DIR, 'logs')
os.makedirs(LOGS_DIR, exist_ok=True)

# Voucher log file
VOUCHER_LOG = os.path.join(LOGS_DIR, 'vouchers.json')

# Detailed log file for analytics
DETAILED_LOG = os.path.join(LOGS_DIR, 'detailed_logs.json')

# File retention period (30 days)
RETENTION_PERIOD = timedelta(days=30)

# Secret key for Flask
SECRET_KEY = os.environ.get('SECRET_KEY', 'dev_key_change_in_production')
