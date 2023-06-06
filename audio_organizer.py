from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import tkinter as tk
import webbrowser
from google_auth_oauthlib.flow import InstalledAppFlow

# Set up the OAuth client ID credentials
flow = InstalledAppFlow.from_client_secrets_file(
    'C:/My Projects/KollasApp/client_secret.json',
    scopes=['https://www.googleapis.com/auth/drive.readonly']
)
creds = flow.run_local_server()

# Save the credentials to a file
token_path = 'C:/My Projects/KollasApp/token.json'
creds.save_to_disk(token_path)

# Create a Google Drive service object
service = build('drive', 'v3', credentials=creds)

# Set the folder ID of the shared folder
folder_url = 'https://drive.google.com/drive/folders/1R03Me1zw4g6r7er3W1xfhldHQAE_v2VP?usp=sharing'
folder_id = folder_url.split('/')[-1]


# Rest of the code...

def get_shared_files(folder_id):
    # Function to perform a recursive search.
    # Retrieves a list of audio files from the shared folder and its subfolders using the Google Drive API.
    # It queries the files with the specified folder ID and MIME type 'audio/*', including files in subfolders.
    audio_files = []

    def traverse_folder(folder_id):
        query = f"'{folder_id}' in parents and mimeType='audio/*'"
        results = service.files().list(q=query, fields="nextPageToken, files(id, name, mimeType)").execute()
        items = results.get('files', [])

        for item in items:
            if item['mimeType'] == 'application/vnd.google-apps.folder':
                traverse_folder(item['id'])
            else:
                audio_files.append(item)

    traverse_folder(folder_id)
    return audio_files

def open_audio_file(file_id): 
    # Takes a file ID as input and constructs the URL to the audio file on Google Drive.
    # It then opens the URL in a new tab of the default web browser.
    audio_url = f"https://drive.google.com/file/d/{file_id}/view?usp=sharing"
    webbrowser.open_new_tab(audio_url)

def main():
    # Serves as the entry point of your program.
    # It calls the get_shared_files() function to obtain the list of audio files and sets up a Tkinter GUI.
    audio_files = get_shared_files(folder_id)  # Pass the folder_id parameter

    if audio_files:
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
    else:
        print("No audio files found in the shared folder.")

if __name__ == "__main__":
    main()