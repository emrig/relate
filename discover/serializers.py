from rest_framework import routers, serializers, viewsets
from .models import Entity, Cluster, Document, ChildEntity

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
    documents = serializers.SerializerMethodField()

    def get_children(self, obj):
        return [{'name': child.name, 'type': child.type} for child in obj.childentity_set.all()]

    def get_documents(self, obj):
        return [{'file_name': document.file_name, 'path': document.path} for document in obj.documents.all()]

    class Meta:
        model = Entity
        fields = ('id', 'type', 'num_docs', 'visible', 'children', 'documents')


class ClusterSerializer(serializers.ModelSerializer):
    entities = EntitySerializer(read_only=True, many=True)

    class Meta:
        model = Cluster
        fields = ('id', 'count', 'entities', 'type', 'algorithm')

class DocumentSerializer(serializers.ModelSerializer):

    class Meta:
        model = Document
        fields = ('id', 'name', 'path')
