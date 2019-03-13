from datetime import timedelta
from discover.models import Entity, Document, Cluster, ChildEntity
from django.db import transaction
from django.db.models import Q, Count
from django.utils import timezone
from django.core import serializers
from relate.settings import TYPES
from discover.serializers import EntitySerializer, ClusterSerializer

BATCH_SIZE = 500
TIME_THRESH = 10

# TODO: If doc already exists
def insert_docs(docs):
    #entries = [Document(path=x['path'], file_name=x['file_name'], status=x['status'], text=x['text']) for x in docs]
    #Document.objects.bulk_create(entries, batch_size=BATCH_SIZE)
    for doc in docs:
        Document.objects.get_or_create(doc)

    return

def num_docs_to_proc():
    return Document.objects.filter(status__exact=0).count()

_doc_status_map = {
    -2: 'Error',
    -1: 'Processing',
    0: 'Pending',
    1: 'Finished'
}

def get_doc_counts():
    result = {}
    total = 0

    for code, message in _doc_status_map.items():
        count = Document.objects.filter(status=code).count()
        total += count
        result[code] = count
    result['total'] = total
    return result

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
                        name=entity['name']
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

# TODO: check if name already exists, come up with flag to include existing and override
@transaction.atomic
def merge_cluster(cluster, name, type):
    documents = []
    # Check if entity already exists
    if Entity.objects.filter(type=type).filter(name=name).count() == 0:
        parent = Entity(name=name, type=type)
        parent.save()
    else:
        parent = Entity.objects.filter(type=type).filter(name=name).get()

    for entity in cluster.entities.all():
        if entity == parent:
            continue
        documents += entity.documents.all()
        obj = ChildEntity(name=entity.name, type=entity.type, entity=parent)
        obj.save()
        entity.delete()
    # Drop any duplicates
    documents = list(set(documents))
    parent.documents.set(documents)
    cluster.status = 'MERGED'
    cluster.save()

def get_related_entities(entity, type, n=10):
    entities = Entity.objects.filter(documents__entity=entity).filter(type=type, visible=True).annotate(total=Count('documents')).order_by('-total')[:n]
    result = [serializers.serialize('json', entity) for entity in entities]
    return result

def get_related_docs(entities):
    ids = [entity.id for entity in entities]
    query = Document.objects.all()

    for id in ids:
        query = query.filter(entity__id=id)

    return query.all()

@transaction.atomic
def get_entity_counts():
    result = {}
    for type in TYPES:
        result[type] = {}
        result[type]['total'] = Entity.objects.filter(type=type).count()
        result[type]['shown'] = Entity.objects.filter(type=type).filter(visible=True).count()
        result[type]['hidden'] = Entity.objects.filter(type=type).filter(visible=False).count()
    return result

@transaction.atomic
def get_top_entities(n=10):
    result = {}
    for type in TYPES:
        entities = Entity.objects.filter(visible=True).filter(type=type).all().annotate(total=Count('documents')).order_by('-total')[:n]
        result[type] = [EntitySerializer(entity).data for entity in entities]

    return result

#TODO: possible bug, hard-coded counts can get out of syn with omitted entities
@transaction.atomic
def get_clusters(n=20):
    result = {}
    for type in TYPES:
        if n != 0:
            clusters = Cluster.objects.all().filter(type=type).annotate(total=Count('count')).order_by('-count')[:n]
        else:
            clusters = Cluster.objects.all().filter(type=type).annotate(total=Count('count')).order_by('-count')
        result[type] = [ClusterSerializer(cluster).data for cluster in clusters]

    return result

@transaction.atomic
def get_entities_for_table(columns, order, start_idx, page_size, search_term, type=None, parents=None, doc_table=False):
    end_idx = start_idx + page_size
    order_by = columns[order['column']]['name']
    order_dir = '-' if order['dir'] == 'desc' else ''
    recordsTotal = Entity.objects.filter(visible=True).all().count()

    if parents:
        parents = list(set(parents))
        parent_objs = Entity.objects.filter(id__in=parents)
        docs = get_related_docs(parent_objs)
    else:
        docs = Document.objects.all()
        parents = []

    if not doc_table:
        query = Entity.objects.filter(visible=True).filter(documents__in=docs).exclude(id__in=parents).annotate(total=Count('documents'))
    else:
        query = Entity.objects.filter(visible=True).filter(documents__in=docs).annotate(total=Count('documents'))

    if search_term:
        query = query.filter(name__icontains=search_term)

    if type:
        query = query.filter(type=type)

    query = query.order_by(f'{order_dir}{order_by}')

    recordsFiltered = query.all().count()
    entities = query.all()[start_idx: end_idx]

    return recordsTotal, recordsFiltered, entities

@transaction.atomic
def get_docs_for_table(columns, order, start_idx, page_size, search_term, parents=None):
    end_idx = start_idx + page_size
    order_by = columns[order['column']]['name']
    order_dir = '-' if order['dir'] == 'desc' else ''
    recordsTotal = Document.objects.all().count()

    if parents:
        parents = list(set(parents))
        parent_objs = Entity.objects.filter(id__in=parents)
        docs = get_related_docs(parent_objs)
    else:
        docs = Document.objects

    if search_term:
        docs = docs.filter(file_name__icontains=search_term)

    recordsFiltered = docs.count()
    docs = docs.order_by(f'{order_dir}{order_by}').all()[start_idx: end_idx]

    return recordsTotal, recordsFiltered, docs

@transaction.atomic
def get_clusters_for_table(columns, order, start_idx, page_size, search_term, type=None):
    end_idx = start_idx + page_size
    order_by = columns[order['column']]['name']
    order_dir = '-' if order['dir'] == 'desc' else ''
    recordsTotal = Cluster.objects.filter(status='PENDING').all().count()

    if search_term:
        clusters = Cluster.objects.filter(status='PENDING').filter(entities__name__icontains=search_term).distinct()
    else:
        clusters = Cluster.objects.filter(status='PENDING').all()

    if type:
        clusters = clusters.filter(type=type)

    recordsFiltered = clusters.count()
    clusters = clusters.order_by(f'{order_dir}{order_by}').all()[start_idx: end_idx]

    return recordsTotal, recordsFiltered, clusters
