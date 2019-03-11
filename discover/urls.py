"""relate URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from .views import *
from rest_framework import routers

urlpatterns = [
    path('', dashboard_view, name='dashboard'),
    path('entity', entity_view, name='entity'),
    path('entity/api', entity_table_api, name='entity_api'),
    path('document/api', document_table_api, name='document_api'),
    path('entity/related', get_related_entities, name='related_entities'),
    path('entity/delete', delete_entities, name='delete_entities'),
    path('resolve', get_clusters, name='resolve'),
    path('resolve/api', cluster_table_api, name='resolve_api'),
    path('resolve/api/merge', merge_cluster_api, name='merge_cluster_api'),
]
