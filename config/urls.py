from django.urls import include, path
from django.views.generic import RedirectView

urlpatterns = [
    path('', RedirectView.as_view(pattern_name='proyectos:lista', permanent=False)),
    path('proyectos/', include('proyectos.urls')),
    path('p/<int:proyecto_id>/', include([
        path('', include('metricas.urls')),
        path('actividades/', include('actividades.urls')),
        path('pruebas/', include('pruebas.urls')),
        path('defectos/', include('defectos.urls')),
        path('importar/', include('importacion.urls')),
        path('reporte/', include('reportes.urls')),
    ])),
]
