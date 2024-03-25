import tkinter as tk
import logging
from pygame import mixer
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import requests
from utils import transform_google_drive_url

def download_google_drive_audio(url):
    try:
        transformed_url = transform_google_drive_url(url)
        response = requests.get(transformed_url)

        if response.status_code == 200:
            with open("temp_audio.mp3", "wb") as f:
                f.write(response.content)
            return "temp_audio.mp3"
        else:
            logging.error(f"Error downloading audio: {response.status_code}")
            return None
    except Exception as e:
        logging.error(f"Error downloading audio: {e}")
        return None

def play_audio_from_url(url):
    audio_filename = download_google_drive_audio(url)
    if audio_filename:
        try:
            # Initialize Pygame mixer once
            if not mixer.get_init():
                mixer.init()

            mixer.music.load(audio_filename)
            mixer.music.play()
        except Exception as e:
            logging.error(f"Error playing audio: {e}")
    else:
        logging.error("Failed to download audio file")

def display_sub_folders_as_buttons(folder_id, parent_frame):
    # Obtain the Google Drive service object
    drive_service = get_service()

    if drive_service:
        # Fetch subfolders and files of the parent folder
        sub_folders_and_files = get_sub_folders_and_files(drive_service, folder_id)

        if sub_folders_and_files:
            # Clear the existing frame
            for widget in parent_frame.winfo_children():
                widget.destroy()

            # Create a frame to hold the buttons
            frame = tk.Frame(parent_frame)
            frame.pack(padx=10, pady=10)

            # Add buttons for each subfolder or audio file
            for item in sub_folders_and_files:
                item_name = item['name']
                item_id = item['id']
                button = tk.Button(frame, text=item_name)
                button.pack(pady=5)

                if item['mimeType'] == 'application/vnd.google-apps.folder':
                    # Recursively call the function for subfolders
                    button.config(command=lambda id=item_id, frame=frame: display_sub_folders_as_buttons(id, frame))
                elif item['mimeType'] == 'audio/mpeg':
                    audio_url = item['webContentLink']
                    logging.info(f"Found audio file: {item_name} - Modified URL: {transform_google_drive_url(audio_url)}")
                    # Play the audio file directly from its URL when the button is pressed
                    button.config(command=lambda url=audio_url: play_audio_from_url(url))

        else:
            logging.info("No sub-folders found.")
    else:
        logging.error("Failed to obtain Google Drive service.")

def play_audio(url):
    audio_filename = download_google_drive_audio(url)
    if audio_filename:
        try:
            # Initialize Pygame mixer once
            if not mixer.get_init():
                mixer.init()

            mixer.music.load(audio_filename)
            mixer.music.play()
        except Exception as e:
            logging.error(f"Error playing audio: {e}")
    else:
        logging.error("Failed to download audio file")
        
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

def get_sub_folders_and_files(service, parent_folder_id=None):
    if parent_folder_id is None:
        query = "trashed=false"
    else:
        query = f"'{parent_folder_id}' in parents and trashed=false"

    folders_and_files = search_files(service, query)

    return folders_and_files

def search_files(service, query):
    MAX_RESULTS = 100
    files = []
    page_token = None
    while True:
        try:
            response = service.files().list(q=query, spaces='drive',
                                            fields='nextPageToken, files(id, name, mimeType, webContentLink)',
                                            pageToken=page_token).execute()
            files.extend(response.get('files', []))
            page_token = response.get('nextPageToken', None)
            if page_token is None or len(files) >= MAX_RESULTS:
                break
        except HttpError as error:
            logging.error(f'An error occurred: {error}')
            break

    return files
