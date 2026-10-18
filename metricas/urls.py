from django.urls import path

from . import views

app_name = 'metricas'
urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('corte/', views.crear_corte, name='crear_corte'),
]
