from utils import transform_google_drive_url
from request import get_sub_folders_and_files
from play_audio import play_audio_from_url
from google_services import get_service
import tkinter as tk
import logging

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
