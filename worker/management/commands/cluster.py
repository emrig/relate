from django.core.management.base import BaseCommand
from django.utils import timezone
from discover.models import Entity, Document, Cluster
from worker.resolution import Clustering
from worker import queries


class Command(BaseCommand):
    help = 'works'

    def add_arguments(self, parser):
        parser.add_argument('total', type=int, help='Indicates the number of users to be created')

    def handle(self, *args, **kwargs):
        t1 = timezone.now()
        type = 'PERSON'
        algorithm = 'lev_slide'

        entities = Entity.objects.all().filter(type=type).prefetch_related('documents')
        entities = [(entity, (entity.alias, len(entity.documents.all()))) for entity in entities]

        # Create cluster object
        clustering = Clustering(algorithm=algorithm, type=type)
        clusters = clustering.get_clusters(entities=entities)

        # Remove clusters of same type, then delete
        Cluster.objects.filter(type=type, algorithm=algorithm).delete()
        queries.insert_clusters(clusters)

        # TODO: test, remove
        clusters = queries.get_clusters(type)

        #merge_cluster(clusters[7][0], 'Ben F Jacoby')
        entity = clusters[7][1][0]
        test1 = [x for x in queries.get_related_entities(entity, 'PERSON')]
        test2 = [x for x in queries.get_related_entities(entity, 'ORGANIZATION')]
        test3 = [x for x in queries.get_related_entities(entity, 'LOCATION')]

        test4 = queries.get_related_docs([entity] + [test1[0]])

        print(timezone.now() - t1)
