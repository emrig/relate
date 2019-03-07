import os


"""
    Main. Loads docs from directory (for now) and calls the Extraction and store pipeline
"""
# Gets all of the files in a directory
def get_file_paths(parent):
    files = []
    for file_or_folder in os.listdir(parent):
        path = os.path.abspath(os.path.join(parent, file_or_folder))
        if os.path.isfile(path):
            files.append({'file_name': file_or_folder, 'path': path})
        else:
            files += get_file_paths(path)
    return files

