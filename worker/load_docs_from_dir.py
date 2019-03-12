import os
import multiprocessing as mp

"""
    Main. Loads docs from directory (for now) and calls the Extraction and store pipeline
"""
# Gets all of the files in a directory
def get_file_paths(parent):
    docs = []
    for file_or_folder in os.listdir(parent):
        path = os.path.abspath(os.path.join(parent, file_or_folder))
        if os.path.isfile(path):
            docs.append({'file_name': file_or_folder, 'path': path})
        else:
            docs += get_file_paths(path)
    return docs

def get_file_text(docs):
    docs_to_proc = []
    for doc in docs:
        try:
            with open(doc['path'], 'r') as f:
                text = f.read()
                doc['status'] = 0
                doc['text'] = text
            docs_to_proc.append(doc)
        # Error reading file
        except Exception as err:
            print(doc['path'], err)
            doc['status'] = -2
            doc['text'] = ''
            docs_to_proc.append(doc)
    return docs_to_proc

