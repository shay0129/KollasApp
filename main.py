<<<<<<< HEAD
#main.py
import tkinter as tk
from request_files import get_shared_folders, create_drive_service, get_files_in_folder
from open_files import open_folder

def custom_order(folder_name):
    # Define the desired order of subfolder names (in Hebrew)
    desired_order = [
        'פסח',
        'ספירת העומר',
        'שבועות',
        'תשעה באב',
        'ימים נוראים',
        'סוכות',
        'שמחת תורה',
        'חנוכה',
        'פורים',
        'שבת'
    ]

    # Extract the subfolder name without the first character
    subfolder_name_without_prefix = folder_name

    # Return the index of the subfolder name in the desired order list
    # Use a very large positive number for non-desired subfolders
    if subfolder_name_without_prefix in desired_order:
        return desired_order.index(subfolder_name_without_prefix)
    else:
        return 999999

def main():
    service = create_drive_service()
    root_folder_id = "1R03Me1zw4g6r7er3W1xfhldHQAE_v2VP"

    sub_folders = get_shared_folders(parent_folder_id=root_folder_id, service=service)

    # Sort the subfolders using the custom ordering function
    sub_folders = sorted(sub_folders, key=lambda folder: custom_order(folder['name']))

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
=======
#main.py
import tkinter as tk
from request_files import get_shared_folders, create_drive_service, get_files_in_folder
from open_files import open_folder

def custom_order(folder_name):
    # Define the desired order of subfolder names (in Hebrew)
    desired_order = [
        'פסח',
        'ספירת העומר',
        'שבועות',
        'תשעה באב',
        'ימים נוראים',
        'סוכות',
        'שמחת תורה',
        'חנוכה',
        'פורים',
        'שבת'
        # Add more subfolder names in the desired order as needed
    ]

    # Extract the subfolder name without the first character
    subfolder_name_without_prefix = folder_name

    # Return the index of the subfolder name in the desired order list
    # Use a very large positive number for non-desired subfolders
    if subfolder_name_without_prefix in desired_order:
        return desired_order.index(subfolder_name_without_prefix)
    else:
        return 999999

def main():
    service = create_drive_service()
    root_folder_id = "1R03Me1zw4g6r7er3W1xfhldHQAE_v2VP"

    sub_folders = get_shared_folders(parent_folder_id=root_folder_id, service=service)

    # Sort the subfolders using the custom ordering function
    sub_folders = sorted(sub_folders, key=lambda folder: custom_order(folder['name']))

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
>>>>>>> 80fe6000d11871e23df84068ec038794e16f55ca
