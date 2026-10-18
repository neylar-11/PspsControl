from django.shortcuts import get_object_or_404, render

from metricas.servicio import corte_solicitado
from metricas.views import ETIQUETAS
from proyectos.models import Proyecto


def reporte(request, proyecto_id):
    """Reporte a fecha de corte: lee la medición guardada (mismos valores que el dashboard)."""
    proyecto = get_object_or_404(Proyecto, pk=proyecto_id)
    corte = corte_solicitado(proyecto, request.GET.get('corte'))
    detalle = corte.detalle if corte else {}
    return render(request, 'reportes/reporte.html', {
        'proyecto': proyecto, 'corte': corte, 'mediciones': corte.mediciones.all() if corte else [],
        'pendientes': detalle.get('pendientes', {}), 'evidencias': detalle.get('evidencias', {}),
        'cortes': proyecto.cortes.all(), 'etiquetas': ETIQUETAS})
