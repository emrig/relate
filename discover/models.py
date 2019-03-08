from django.db import models
import uuid

# Create your models here.

class Document(models.Model):
    """
        Status:
            -2: Error Processing
            -1: Processing
            0: Ready for processing
            1: Done Processing
    """
    text = models.TextField()
    status = models.IntegerField()
    file_name = models.CharField(max_length=300, null=True)
    path = models.CharField(max_length=300, primary_key=True)
    last_update = models.DateTimeField(null=True, auto_now=True)

class Entity(models.Model):
    name = models.CharField(max_length=300)
    type = models.CharField(max_length=20)
    documents = models.ManyToManyField(Document)
    visible = models.BooleanField(default=True)

    @property
    def num_docs(self):
        return self.documents.count()

class ChildEntity(models.Model):
    entity = models.ForeignKey(Entity, on_delete=models.CASCADE)
    name = models.CharField(max_length=300)
    type = models.CharField(max_length=20)

"""
class FoundIn(models.Model):
    entity = models.ForeignKey(Entity, on_delete=models.CASCADE)
    document = models.ForeignKey(Document, on_delete=models.CASCADE)
    """

"""
class FoundIn(models.Model):
    entity = models.ManyToManyField(Entity, on_delete=models.CASCADE)
    document = models.ManyToManyField(Document, on_delete=models.CASCADE)
"""

class Cluster(models.Model):
    entities = models.ManyToManyField(Entity)
    type = models.CharField(null=True, max_length=20)
    count = models.IntegerField()
    status = models.CharField(max_length=20)
    algorithm = models.CharField(max_length=20)



