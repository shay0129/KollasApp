# Takes buttons from display, and show it on tkinter window
import tkinter as tk
import logging
from display import display_sub_folders_as_buttons
def main():
    logging.basicConfig(level=logging.INFO)

    # Specify the root folder ID of the Google Drive folder
    root_folder_id = '1R03Me1zw4g6r7er3W1xfhldHQAE_v2VP'

    # Create the main window
    root = tk.Tk()
    root.geometry("500x500")
    root.title("Google Drive Folders")

    # Create a frame to hold the buttons
    frame = tk.Frame(root)
    frame.pack(padx=10, pady=10)

    # Create a button to view subfolders
    view_button = tk.Button(frame, text="View Sub-folders", command=lambda: display_sub_folders_as_buttons(root_folder_id, frame))
    view_button.pack()

    root.mainloop()

if __name__ == "__main__":
    main()
