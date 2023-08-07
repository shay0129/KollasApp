# request_files.py
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from credentials import load_google_credentials

def create_drive_service():
    credentials = load_google_credentials()
    service = build('drive', 'v3', credentials=credentials)
    return service

def search_file(service, query):
    MAX_RESULTS = 100
    files = []
    page_token = None
    while True:
        try:
            response = service.files().list(q=query, spaces='drive',
                                            fields='nextPageToken, files(id, name, mimeType)',
                                            pageToken=page_token).execute()
            for file in response.get('files', []):
                files.append(file)
                print(F'Found file: {file.get("name")}, {file.get("id")}')
            if len(files) >= MAX_RESULTS:
                print(f"Found more than {MAX_RESULTS} files; stopping search.")
                break
            page_token = response.get('nextPageToken', None)
            if page_token is None:
                break
        except HttpError as error:
            print(F'An error occurred: {error}')
            files = []
            break

    return files

def get_shared_folders(parent_folder_id=None, service=None):
    if parent_folder_id is None:
        query = "mimeType='application/vnd.google-apps.folder' and trashed=false"
    else:
        query = f"'{parent_folder_id}' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false"

    folders = search_file(service, query)

    print("Retrieved sub-folders:")
    for folder in folders:
        print(folder['name'], folder['id'])

    return folders

def get_files_in_folder(folder_id, service):
    # Fetch the folder contents from Google Drive
    query = f"'{folder_id}' in parents and trashed = false"
    items = search_file(service, query)

    files_and_folders = []
    for item in items:
        files_and_folders.append({"name": item["name"], "id": item["id"], "is_folder": item["mimeType"] == "application/vnd.google-apps.folder"})

    return files_and_folders

def get_audio_data(file_id, service):
    request = service.files().get_media(fileId=file_id)
    response = request.execute()

<<<<<<< HEAD
    return response
=======
    return response
>>>>>>> 80fe6000d11871e23df84068ec038794e16f55ca
