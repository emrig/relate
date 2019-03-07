from django.core.management.base import BaseCommand
from datetime import datetime
from worker.load_docs_from_dir import get_file_paths
from worker.queries import insert_docs

class Command(BaseCommand):
    help = 'works'

    def add_arguments(self, parser):
        parser.add_argument('total', type=int, help='Indicates the number of users to be created')

    def handle(self, *args, **kwargs):
        print('GETTING DOCS', kwargs['total'])
        directory = 'C:/Github/Masters/enron/maildir'
        t1 = datetime.now()

        docs = get_file_paths(directory)
        insert_docs(docs)

        print(datetime.now() - t1)
