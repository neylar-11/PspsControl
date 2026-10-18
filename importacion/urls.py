from django.urls import path

from . import views

app_name = 'importacion'
urlpatterns = [
    path('', views.importar, name='importar'),
    path('plantilla/<str:tipo>/', views.plantilla, name='plantilla'),
]
