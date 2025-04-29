from django.urls import path
from . import views
from django.conf.urls.static import static
from django.conf import settings

urlpatterns = [
    path('', views.index, name='index'),
    path('context/', views.generate_context, name='context'),
    path('lattice/', views.generate_lattice, name='lattice'),
    path('mapping/', views.apply_mapping_rules, name='mapping'),
    path('graph/', views.graph, name='graph'),
    path('owl/', views.export_owl, name='owl'),
] + static('/', document_root=settings.BASE_DIR)
