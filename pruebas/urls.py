from django.urls import path

from . import views

app_name = 'pruebas'
urlpatterns = [
    path('', views.lista, name='lista'),
    path('nueva/', views.crear, name='crear'),
    path('<int:pk>/editar/', views.editar, name='editar'),
    path('<int:pk>/resultado/', views.resultado, name='resultado'),
]
