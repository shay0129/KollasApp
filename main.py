#main.py
import tkinter as tk
from request_files import get_shared_folders, create_drive_service, get_files_in_folder
from open_files import open_folder

def extract_numeric_prefix(folder_name):
    # Try to extract a numeric prefix from the folder name
    try:
        # Split the folder name by the first dot and convert the first part to an integer
        numeric_prefix = int(folder_name.split('.', 1)[0])
        return numeric_prefix
    except ValueError:
        # If a numeric prefix cannot be extracted, return a large number
        return float('inf')

def main():
    service = create_drive_service()
    parent_folder_id = "1R03Me1zw4g6r7er3W1xfhldHQAE_v2VP"

    sub_folders = get_shared_folders(parent_folder_id=parent_folder_id, service=service)

    # Sort the subfolders using the numeric prefix as the sorting key
    sub_folders = sorted(sub_folders, key=lambda folder: extract_numeric_prefix(folder['name']))

    root = tk.Tk()
    root.geometry("500x800")
    root.title("List of Sub-folders")

    label = tk.Label(root, text="List of sub-folders:", font=('Arial', 12))
    label.pack(padx=10, pady=10)

    for i, folder in enumerate(sub_folders):
        folder_name = folder['name']
        button = tk.Button(root, text=folder_name, font=('Arial', 18),
                   command=lambda folder_id=folder['id'], folder_name=folder_name: open_folder(folder_id, service, root, folder_name))
        button.pack()

    root.mainloop()

if __name__ == "__main__":
    main()
