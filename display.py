# display.py
# Contains function to display subfolders and files as buttons
import tkinter as tk
from google_services import get_service, get_sub_folders_and_files
import logging
from tkinter import ttk
from play_audio import play_audio_from_url
from utils import transform_google_drive_url
import os

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

            # Function to go back to the previous page
            def go_back():
                # Destroy the current frame
                frame.destroy()

                # Extract the parent folder ID from the current folder's path
                parent_folder_id = os.path.dirname(folder_id)

                # If the parent folder ID is empty, set it to None to indicate the root folder
                if not parent_folder_id:
                    parent_folder_id = None

                # Create a new frame within the parent frame
                new_frame = tk.Frame(parent_frame)
                new_frame.pack(padx=10, pady=10)

                # Display subfolders and files in the parent folder
                display_sub_folders_as_buttons(parent_folder_id, parent_frame)

            # Create and pack the "Go Back" button
            back_button = tk.Button(frame, text="Go Back", command=go_back)
            back_button.pack()

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
                    play_button = ttk.Button(frame, text="Play", command=lambda url=audio_url: play_audio_from_url(url))
                    play_button.pack(pady=5)

        else:
            logging.info("No sub-folders found.")
    else:
        logging.error("Failed to obtain Google Drive service.")
