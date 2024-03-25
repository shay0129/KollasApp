# Gets credentials, load it and build a service object

import logging
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

def load_google_credentials():
    # Hardcode the path to the Google credentials JSON file
    credentials_path = "C:/My Projects/KollasApp/secret_files/config/kollas_app_service_account.json"

    try:
        # Load credentials from the JSON file
        credentials = Credentials.from_service_account_file(credentials_path, scopes=['https://www.googleapis.com/auth/drive'])
        logging.info("Credentials loaded successfully!")
        return credentials
    except Exception as e:
        logging.error(f"Error loading credentials: {e}")
        return None

def get_service():
    # Load Google Drive credentials
    my_credentials = load_google_credentials()

    if my_credentials:
        # Build the Google Drive service object
        drive_service = build('drive', 'v3', credentials=my_credentials)
        return drive_service
    else:
        logging.error("Failed to load Google Drive credentials!")
        return None
