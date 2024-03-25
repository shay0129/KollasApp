# request.py
# Request folders and audio files from Google's server, download a temporary file by url, and play it
from googleapiclient.errors import HttpError
from utils import transform_google_drive_url
import logging
import requests

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

def get_sub_folders_and_files(service, parent_folder_id=None):
    if parent_folder_id is None:
        query = "trashed=false"
    else:
        query = f"'{parent_folder_id}' in parents and trashed=false"

    folders_and_files = search_files(service, query)

    return folders_and_files

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
