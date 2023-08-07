# credentials.py
import os
from dotenv import load_dotenv
from google.oauth2.service_account import Credentials

def load_google_credentials():
    CREDENTIALS_PATH = None
    try:
        load_dotenv()
        CREDENTIALS_PATH = os.getenv('GOOGLE_CREDENTIALS_PATH')
        if CREDENTIALS_PATH is not None:
            print("Found CREDENTIALS_PATH in the .env file")
    except ImportError:
        print("dotenv library is not installed.")
        pass
    
    if CREDENTIALS_PATH is None:
        CREDENTIALS_PATH = "C:/My Projects/KollasApp/audio_file_manager_service_account.json"
    credentials = Credentials.from_service_account_file(CREDENTIALS_PATH, scopes=['https://www.googleapis.com/auth/drive.readonly'])
    return credentials