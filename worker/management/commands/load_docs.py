from django.core.management.base import BaseCommand
from datetime import datetime
from worker.load_docs_from_dir import get_new_docs, get_file_text
from worker.queries import insert_docs
from relate.settings import DOC_DIR, FILE_READ_BATCH_SIZE, TYPES, CLUSTERING_ALGORITHMS
from discover.models import Entity, Cluster, Document
from worker import queries
import os
from worker.worker import parse
from worker.resolution import Clustering
from time import sleep

class Command(BaseCommand):
    help = ''

    def add_arguments(self, parser):
        parser.add_argument('actions', type=str, help='Indicates the number of users to be created')

    def handle(self, *args, **kwargs):

        actions = str(kwargs['actions']).split(',')

        print('Actions:', ', '.join(actions))

        # Wait for db to initialize
        sleep(10)

        if 'load' in actions:
            directory = os.path.abspath(DOC_DIR)
            print(f'Scanning Documents in {directory}')

            t1 = datetime.now()
            docs = get_new_docs(directory)

            while len(docs) > 0:
                batch = docs[:FILE_READ_BATCH_SIZE]
                docs = docs[FILE_READ_BATCH_SIZE:]

                batch = get_file_text(batch)

                t2 = datetime.now()
                insert_docs(batch)
                print('Document insertion batch size', FILE_READ_BATCH_SIZE, 'took:', datetime.now() - t2)

            print(datetime.now() - t1)

        if 'extract' in actions:
            print('Extracting entities from documents..')
            parse()

        if 'cluster' in actions:
            t1 = datetime.now()

            for type in TYPES:
                for algorithm in CLUSTERING_ALGORITHMS:
                    print('Resolving names of type', type, 'using algorithm', algorithm)

                    # Get entity names
                    entities = Entity.objects.all().filter(type=type, visible=True)
                    entities = [(entity, (entity.name, 0)) for entity in entities]

                    # Create cluster object
                    clustering = Clustering(algorithm=algorithm, type=type)
                    clusters = clustering.get_clusters(entities=entities)

                    # Remove clusters of same type, then delete
                    Cluster.objects.filter(type=type, algorithm=algorithm).delete()
                    queries.insert_clusters(clusters)

            # add counts of total documents in cluster. Faster to do this after clustering.
            queries.add_cluster_counts()

            print(datetime.now() - t1)
