from rest_framework import routers, serializers, viewsets
from .models import Entity, Cluster, Document, ChildEntity
from django.forms.models import model_to_dict

class ChildEntitySerializer(serializers.ModelSerializer):
    class Meta:
        model = ChildEntity
        fields = ('name', 'type')

class DocumentOnlySerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = ('id', 'name', 'path')

class EntitySerializer(serializers.ModelSerializer):
    children = serializers.SerializerMethodField()

    def get_children(self, obj):
        return [{'name': child.name, 'type': child.type} for child in obj.childentity_set.all()]

    class Meta:
        model = Entity
        fields = ('id', 'name', 'type', 'num_docs', 'visible', 'children')


class ClusterSerializer(serializers.ModelSerializer):
    entities = EntitySerializer(read_only=True, many=True)
    #entities = model_to_dict(entities)

    class Meta:
        model = Cluster
        fields = ('id', 'count', 'entities', 'type', 'algorithm')

class DocumentSerializer(serializers.ModelSerializer):

    class Meta:
        model = Document
        fields = ('id', 'name', 'path')


class EntityPageSerializer(serializers.ModelSerializer):
    children = serializers.SerializerMethodField()
    documents = serializers.SerializerMethodField()
    clusters = serializers.SerializerMethodField()

    def get_clusters(self, obj):
        return [ClusterSerializer(cluster).data for cluster in obj.cluster_set.all()]

    def get_children(self, obj):
        return [{'name': child.name, 'type': child.type} for child in obj.childentity_set.all()]

    def get_documents(self, obj):
        return [{'file_name': document.file_name, 'path': document.path} for document in obj.documents.all()]

    class Meta:
        model = Entity
        fields = ('id', 'name', 'type', 'num_docs', 'visible', 'children', 'documents', 'clusters')
