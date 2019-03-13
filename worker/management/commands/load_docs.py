from django.core.management.base import BaseCommand
from datetime import datetime
from worker.load_docs_from_dir import get_file_paths, get_file_text
from worker.queries import insert_docs
from relate.settings import DOC_DIR, FILE_READ_BATCH_SIZE, TYPES, CLUSTERING_ALGORITHM
from discover.models import Entity, Cluster
from worker import queries
import os
from worker.worker import parse
from worker.resolution import Clustering

class Command(BaseCommand):
    help = 'works'

    def add_arguments(self, parser):
        parser.add_argument('status', type=int, help='Indicates the number of users to be created')

    def handle(self, *args, **kwargs):
        directory = os.path.abspath(DOC_DIR)
        print(f'Scanning Documents in {directory}', kwargs['status'])

        t1 = datetime.now()
        docs = get_file_paths(directory)

        while len(docs) > 0:
            batch = docs[:FILE_READ_BATCH_SIZE]
            docs = docs[FILE_READ_BATCH_SIZE:]

            batch = get_file_text(batch)

            t2 = datetime.now()
            insert_docs(batch)
            print('Batch size', FILE_READ_BATCH_SIZE, 'took:', datetime.now() - t2)

        print(datetime.now() - t1)

        print('Extracting entities from documents..')

        parse()

        t1 = datetime.now()

        for type in TYPES:
            print('Resolving names of type', type)
            algorithm = CLUSTERING_ALGORITHM

            # Get document counts
            entities = Entity.objects.all().filter(type=type, visible=True).prefetch_related('documents')
            entities = [(entity, (entity.name, len(entity.documents.all()))) for entity in entities]

            # Create cluster object
            clustering = Clustering(algorithm=algorithm, type=type)
            clusters = clustering.get_clusters(entities=entities)

            # Remove clusters of same type, then delete
            Cluster.objects.filter(type=type, algorithm=algorithm).delete()
            queries.insert_clusters(clusters)

        print(datetime.now() - t1)
