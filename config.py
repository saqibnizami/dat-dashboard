import os

from vault import secrets

LOGGING_APP_NAME = "ubiome-dat-dashboard"
SECRETS = secrets.load(LOGGING_APP_NAME)
# convert secrets into variables
locals().update(SECRETS)

# Define the application directory
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
