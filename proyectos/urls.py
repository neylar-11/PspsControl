from django.urls import path

from . import views

app_name = 'proyectos'
urlpatterns = [
    path('', views.lista, name='lista'),
    path('nuevo/', views.crear, name='crear'),
    path('<int:pk>/editar/', views.editar, name='editar'),
    path('<int:pk>/confirmar-defectos/', views.confirmar_defectos, name='confirmar_defectos'),
]
