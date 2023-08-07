# open_files.py
import tkinter as tk
from request_files import get_files_in_folder
<<<<<<< HEAD
import webbrowser
=======
>>>>>>> 80fe6000d11871e23df84068ec038794e16f55ca

files_and_folders = []

def open_folder(folder_id, service, parent_window, folder_name):
    def on_listbox_double_click(event):
        global files_and_folders  # Declare the variable as global to access the outer variable
        selected_index = listbox.curselection()
        if selected_index:
            selected_item = listbox.get(selected_index)
            # Extract the folder name without the '[Folder] ' prefix
            selected_item = selected_item.split('[Folder] ')[-1]
            for item in files_and_folders:
                if item['name'] == selected_item and item['is_folder']:
                    item_id = item['id']
                    files_and_folders = get_files_in_folder(item_id, service)
                    update_listbox(files_and_folders)
                    break
<<<<<<< HEAD
                elif item['name'] == selected_item and item['is_audio']:  # Check if the selected item is an audio file
                    audio_url = get_audio_url(item['id'], service)
                    if audio_url:
                        webbrowser.open(audio_url)
=======
>>>>>>> 80fe6000d11871e23df84068ec038794e16f55ca

    def update_listbox(files_and_folders):
        listbox.delete(0, tk.END)  # Clear the listbox
        for item in files_and_folders:
            if item['is_folder']:
                # Show sub-folders first in the list
                listbox.insert(0, f"[Folder] {item['name']}")
            else:
                listbox.insert(tk.END, f"[File] {item['name']}")

    global files_and_folders  # Declare the variable as global to access the outer variable
    files_and_folders = get_files_in_folder(folder_id, service)

    folder_window = tk.Toplevel(parent_window)
    folder_window.geometry("500x400")
    folder_window.title(f"List of Files and Folders in {folder_name}")

    label = tk.Label(folder_window, text=f"List of files and folders in {folder_name}", font=('Arial', 12))
    label.pack(padx=10, pady=10)

    listbox = tk.Listbox(folder_window, width=50, height=20, font=('Arial', 12))
    listbox.pack(padx=10, pady=10)

    update_listbox(files_and_folders)

    listbox.bind("<Double-Button-1>", on_listbox_double_click)
<<<<<<< HEAD

def get_audio_url(file_id, service):
    try:
        file = service.files().get(fileId=file_id, fields="webContentLink").execute()
        return file.get('webContentLink')
    except Exception as e:
        print("Error getting audio URL:", e)
        return None
=======
>>>>>>> 80fe6000d11871e23df84068ec038794e16f55ca
