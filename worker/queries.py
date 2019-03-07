from datetime import timedelta
from discover.models import Entity, Document, Cluster
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from django.db.models import Count

BATCH_SIZE = 500
TIME_THRESH = 10

def insert_docs(docs):
    entries = [Document(path=x['path'], file_name=x['file_name'], status=0) for x in docs]
    Document.objects.bulk_create(entries, batch_size=BATCH_SIZE)

def num_docs_to_proc():
    return Document.objects.filter(status__exact=0).count()

@transaction.atomic
def get_docs_to_proc(n=BATCH_SIZE):
    # Retrieve and set status flag
    docs_to_proc = []
    c1 = Q(status__exact=0)
    c2 = Q(status__exact=-1)
    c3 = Q(last_update__lte=timezone.now()-timedelta(minutes=TIME_THRESH))
    docs = Document.objects.select_for_update().filter((c1 | (c2 & c3))).order_by('?')[:n]
    for doc in docs:
        docs_to_proc.append(doc)
        doc.status = -1
        doc.last_update = timezone.now()
        doc.save()
    return docs_to_proc

def insert_entities(entities, doc):
    try:
        with transaction.atomic():
            for entity in entities:
                # Filter out any long names, probably an NER error
                if len(entity['name']) <= Entity._meta.get_field('name').max_length:
                    obj, created = Entity.objects.get_or_create(
                        type=entity['type'],
                        name=entity['name'],
                        defaults={'alias': entity['name']}
                    )
                    obj.documents.add(doc)
            doc.status = 1
            doc.save()
        return True
    except Exception as err:
        print(err)
        return False

def insert_clusters(clusters):
    try:
        with transaction.atomic():
            for cluster in clusters:
                obj = Cluster(
                    type=cluster['type'], algorithm=cluster['algorithm'], status=cluster['status'], count=cluster['count'])
                obj.save()
                obj.entities.set(cluster['entities'])
                obj.save()
        return True
    except Exception as err:
        print(err)
        return False

def get_clusters(type):
    clusters = Cluster.objects.all().filter(type=type).prefetch_related('entities')
    return [(cluster, cluster.entities.all()) for cluster in clusters]

@transaction.atomic
def merge_cluster(cluster, alias):
    for entity in cluster.entities.all():
        entity.alias = alias
        entity.save()
    cluster.status = 'MERGED'
    cluster.save()

def get_related_entities(entity, type):
    entities = Entity.objects.filter(documents__entity=entity).filter(type=type)
    return entities

def get_related_docs(entities):
    ids = [entity.id for entity in entities]
    query = Document.objects.all()

    for id in ids:
        query = query.filter(entity__id=id)

    return query.all()
