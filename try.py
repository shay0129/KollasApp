import tkinter as tk
import webbrowser
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

from googleapiclient.errors import HttpError
import os

#### LOAD CREDENTIALS
CREDENTIALS_PATH = None
try:
    # I SET THIS UP SO WE CAN USE .ENV 
    # IT IS UNDER A TRY BLOCK SO IT STILL WORKS, BUT WE CAN FIX THIS
    from dotenv import load_dotenv
    load_dotenv()  # get the accouunt from credentials (saved in .env, which is not tracked by git)
    CREDENTIALS_PATH = os.getenv('GOOGLE_CREDENTIALS_PATH')
    if CREDENTIALS_PATH is not None:
        print("Found CREDENTIALS_PATH in the .env file")
except:
    print("do not have dotenv installed")
    pass

if CREDENTIALS_PATH is None:
    # have your default one here
    CREDENTIALS_PATH="C:/My Projects/KollasApp/audio_file_manager_service_account.json"


# Set up the service account credentials
credentials = Credentials.from_service_account_file(
    CREDENTIALS_PATH
    ,
    scopes=['https://www.googleapis.com/auth/drive.readonly']
)

# Create a Google Drive service object
service = build('drive', 'v3', credentials=credentials)

# Set the folder ID of the shared folder
folder_id = '1R03Me1zw4g6r7er3W1xfhldHQAE_v2VP'



####   HELPER FUCTION TO LIST FILES GIVEN A QUERY

def execute_drive_query(query):
    """Make using the google api a bit easier
    gets all the files
    see: https://developers.google.com/drive/api/guides/search-files
    """
    MAX_RESULTS = 100  # max number of results to return, so it doesnt take too long if you have a TON of files
    try:
        files = []
        page_token = None
        while True:
            # pylint: disable=maybe-no-member
            response = service.files().list(q=query, pageToken=page_token).execute()
            for file in response.get('files', []):
                # Process change
                print(F'Found file: {file.get("name")}, {file.get("id")}')
            files.extend(response.get('files', []))
            if len(files) >= MAX_RESULTS:
                print(f"Found more than {MAX_RESULTS} files; stopping search.")
                break
            page_token = response.get('nextPageToken', None)
            if page_token is None:
                break

    except HttpError as error:
        print(F'An error occurred: {error}')
        files = None

    return files


def list_all_audio_files():
    #  This Query Works For Me.  
    #  You need to make sure the folder is shared with your service account email (in your credentails folder)
    # I'm not sure how to get by parent folder ID; you my need first search for the folder and then use that to get files?  Not sure.
    query = f"mimeType='audio/mpeg'"
    audio_files = execute_drive_query(query)#, fields="files(id, name)")
    # audio_files = results.get('files', [])

    print("Retrieved audio files:")
    for file in audio_files:
        print(file['name'], file['id'])

    return audio_files


def get_shared_files():
    # Retrieves a list of audio files from the shared folder using the Google Drive API.
    # It queries the files with the specified folder ID and MIME type 'audio/*'.
    query = f"'{folder_id}' in parents and mimeType='audio/*'"
    results = service.files().list(q=query, fields="files(id, name)").execute()
    audio_files = results.get('files', [])

    print("Retrieved audio files:")
    breakpoint()
    for file in audio_files:
        print(file['name'], file['id'])

    return audio_files


def open_audio_file(file_id):
    # Takes a file ID as input and constructs the URL to the audio file on Google Drive.
    # It then opens the URL in a new tab of the default web browser.
    audio_url = f"https://drive.google.com/file/d/{file_id}/view?usp=sharing"
    webbrowser.open_new_tab(audio_url)

def main():
    # Serves as the entry point of your program.
    # It calls the get_shared_files() function to obtain the list of audio files and sets up a Tkinter GUI.
    # audio_files = get_shared_files()

    # HEY SHAI, I changed this line;
    audio_files = list_all_audio_files()



    # Create a simple Tkinter GUI to display the file names
    root = tk.Tk()

    def button_click(file_id):
        # Assigned to each "Listen" button.
        # It takes the file ID as a parameter and calls the open_audio_file() function, passing the file ID.
        # This function opens the audio file in the web browser when the button is clicked.
        open_audio_file(file_id)

    for i, file in enumerate(audio_files):
        label = tk.Label(root, text=f"{i+1}. {file['name']}")
        label.pack()
        button = tk.Button(root, text="Listen", command=lambda file_id=file['id']: button_click(file_id))
        button.pack()

    root.mainloop()

if __name__ == "__main__":
    # Condition checks if the script is being run directly (not imported as a module).
    # If so, it calls the main() function to start the program.
    main()
