from django.shortcuts import render
from django.http import HttpResponse
from django.views.generic import TemplateView, CreateView
from rest_framework.decorators import api_view, renderer_classes
from rest_framework.renderers import JSONRenderer
from django.core import serializers
from .serializers import EntitySerializer, ClusterSerializer
from .models import Entity, Document, Cluster
from worker import queries
import json

NUM_TOP_ENTITIES = 10

class HomePageTemplateView(TemplateView):
    template_name = 'dashboard.html'

@api_view(['POST'])
@renderer_classes((JSONRenderer,))
def entity_table_api(request):
    args = json.loads(request.data.get("args"))

    search_term = args['search']['value']
    start_idx = args['start']
    page_size = args['length']
    order = args['order'][0]
    type = args.get('type', None)
    columns = args.get('columns')
    parents = args.get('parents', None)
    doc_table = args.get('doc_table', None)

    recordsTotal, recordsFiltered, data = \
        queries.get_entities_for_table(columns, order, start_idx, page_size, search_term, type, parents, doc_table)

    ret = {}
    ret['draw'] = args['draw']
    ret['recordsTotal'] = recordsTotal
    ret['recordsFiltered'] = recordsFiltered
    ret['data'] = [[_make_entity_url(EntitySerializer(x).data), x.total, x.type, x.id, x.name] for x in data]

    return HttpResponse(json.dumps(ret), content_type='application/json')

@api_view(['POST'])
@renderer_classes((JSONRenderer,))
def document_table_api(request):
    args = json.loads(request.data.get("args"))

    search_term = args['search']['value']
    start_idx = args['start']
    page_size = args['length']
    order = args['order'][0]
    columns = args.get('columns')
    parents = args.get('parents', None)

    recordsTotal, recordsFiltered, data = \
        queries.get_docs_for_table(columns, order, start_idx, page_size, search_term, parents)

    ret = {}
    ret['draw'] = args['draw']
    ret['recordsTotal'] = recordsTotal
    ret['recordsFiltered'] = recordsFiltered
    ret['data'] = [[x.file_name, x.path] for x in data]

    return HttpResponse(json.dumps(ret), content_type='application/json')

@api_view(['GET', 'POST'])
@renderer_classes((JSONRenderer,))
def cluster_table_api(request):
    args = json.loads(request.data.get("args"))

    search_term = args['search']['value']
    start_idx = args['start']
    page_size = args['length']
    order = args['order'][0]
    type = args.get('type', None)
    columns = args.get('columns')

    recordsTotal, recordsFiltered, clusters = \
        queries.get_clusters_for_table(columns, order, start_idx, page_size, search_term, type)

    ret = {}
    ret['draw'] = args['draw']
    ret['recordsTotal'] = recordsTotal
    ret['recordsFiltered'] = recordsFiltered

    data = json.loads(json.dumps([ClusterSerializer(cluster).data for cluster in clusters]))
    ret['data'] = [
        ['<br>'.join([_make_entity_url(entity) for entity in x['entities']]), x['count'], x['type'], x['id']]
        for x in data]

    return HttpResponse(json.dumps(ret), content_type='application/json')

class PersonCreateView(CreateView):
    model = Entity
    fields = ('alias', 'type')

@api_view(['GET'])
def dashboard_view(request):
    # Returns statistics about the document workspace
    ret = {}
    ret['doc_counts'] = queries.get_doc_counts()
    ret['entity_count'] = queries.get_entity_counts()
    ret['top_entities'] = queries.get_top_entities(NUM_TOP_ENTITIES)
    ret['cluster_count'] = Cluster.objects.filter(status='PENDING').count()
    ret['top_clusters'] = queries.get_clusters()

    return render(request, 'dashboard.html', context=ret)

@api_view(['GET' ,'POST'])
def entity_view(request):
    ret = {'selected_entity': {}}
    id = request.query_params.get('id', None)
    if id:
        ret['selected_entity']['id'] = id
        ret['selected_entity']['name'] = request.query_params.get('name', None)
        ret['selected_entity']['type'] = request.query_params.get('type', None)
        ret['selected_entity'] = json.dumps(ret['selected_entity'])
    return render(request, 'entity.html', context=ret)

@api_view(['GET'])
#@renderer_classes((JSONRenderer,))
def document_view(request):
    # Returns statistics about the document workspace
    ret = {'document': {}}
    path = request.query_params.get('path', None)

    if path:
        ret['document']['path'] = path
        ret['document']['file_name'] = request.query_params.get('file_name', None)
        doc = Document.objects.get(path=path)
    else:
        doc = Document.objects.all()[0]
        ret['document']['path'] = doc.path
        ret['document']['file_name'] = doc.file_name

    ret['document']['text'] = doc.text
    ret['document']['entities'] = [EntitySerializer(entity) for entity in doc.entity_set.all()]
    ret['document']['selected_entities'] = [entity.id for entity in doc.entity_set.all()]

    return render(request, 'document.html', context=ret)

@api_view(['GET'])
@renderer_classes((JSONRenderer,))
def get_clusters(request):
    ret = {}
    clusters = queries.get_clusters()
    # convert OrderedDict to dict
    ret['clusters'] = json.loads(json.dumps(clusters))

    return render(request, 'resolve.html', context=ret)

@api_view(['POST'])
@renderer_classes((JSONRenderer,))
def merge_cluster_api(request):
    cluster = request.data['cluster']
    cluster_obj = Cluster.objects.get(id=cluster['id'])
    queries.merge_cluster(cluster_obj, cluster['new_name'], cluster['type'])

    return HttpResponse(status=204)

@api_view(['GET'])
@renderer_classes((JSONRenderer,))
def get_related_entities(request):
    id = json.loads(request.query_params['id'])
    entity = Entity.objects.filter(id=id).get()
    result = queries.get_related_entities(entity, 'PERSON')
    response = serializers.serialize('json', result)

    return HttpResponse(response, content_type='application/json')

@api_view(['GET'])
@renderer_classes((JSONRenderer,))
def delete_entities(request):
    ids = json.loads(request.query_params['ids'])
    result = Entity.objects.filter(id__in=ids).update(visible=False)

    return HttpResponse('SUCCESS')

def _make_entity_url(entity):
    return f"<a href='entity?id={entity['id']}&name={entity['name']}&type={entity['type']}'>{entity['name']}</a>"

@api_view(['POST'])
def entity_api(request):
    args = json.loads(request.data.get("args"))

    search_term = args['search']['value']
    start_idx = args['start']
    page_size = args['length']
    order = args['order'][0]
    type = args.get('type', None)
    columns = args.get('columns')
    parents = args.get('parents', None)

    recordsTotal, recordsFiltered, data = \
        queries.get_entities(columns, order, start_idx, page_size, search_term, type, parents)

    ret = {}
    ret['draw'] = args['draw']
    ret['recordsTotal'] = recordsTotal
    ret['recordsFiltered'] = recordsFiltered
    ret['data'] = [[_make_entity_url(EntitySerializer(x).data), x.total, x.type, x.id, x.name] for x in data]

    return HttpResponse(json.dumps(ret), content_type='application/json')
