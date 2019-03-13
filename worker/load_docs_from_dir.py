import os
import multiprocessing as mp
from discover.models import Document
"""
    Main. Loads docs from directory (for now) and calls the Extraction and store pipeline
"""

existing_docs = set([os.path.abspath(x['path']) for x in Document.objects.values('path')])

def get_new_docs(parent):

    all_docs = get_file_paths(parent)
    print('Found', len(all_docs), 'documents in')
    new_docs = [x for x in all_docs if x['path'] not in existing_docs]
    print('Inserting', len(new_docs), 'documents into database.')

    return new_docs

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

