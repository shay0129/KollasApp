# credentials.py
import os
from dotenv import load_dotenv
from google.oauth2.service_account import Credentials

def load_google_credentials():
    # Combine environment variables with default values
    dotenv_path = os.path.join("C:/My Projects/KollasApp/secret/", '.env')
    load_dotenv(dotenv_path)
    print("dotenv succeeded")
    CREDENTIALS_PATH = os.getenv('GOOGLE_CREDENTIALS_PATH')
    
    if CREDENTIALS_PATH is not None:
        print("Found CREDENTIALS_PATH in the .env file")
    else:
        print("Using default path")
        CREDENTIALS_PATH = "C:/My Projects/KollasApp/secret/audio_file_manager_service_account.json"
    
    try:
        credentials = Credentials.from_service_account_file(CREDENTIALS_PATH, scopes=['https://www.googleapis.com/auth/drive.readonly'])
        print("Credentials are good")
        return credentials
    except Exception as e:
        print(f"Error loading credentials: {e}")
        return None

