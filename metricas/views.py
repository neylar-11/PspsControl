from datetime import datetime

from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from proyectos.models import Proyecto
from .servicio import corte_solicitado, registrar_corte

ETIQUETAS = {'verde': 'Verde', 'amarillo': 'Amarillo', 'rojo': 'Rojo', 'gris': 'Sin datos', 'no_aplica': 'No aplica'}


def dashboard(request, proyecto_id):
    proyecto = get_object_or_404(Proyecto, pk=proyecto_id)
    corte = corte_solicitado(proyecto, request.GET.get('corte'))
    cortes = list(proyecto.cortes.order_by('fecha_corte'))
    grafica = {'fechas': [str(c.fecha_corte) for c in cortes], 'series': {}}
    for c in cortes:
        valores = {m.clave: m.valor for m in c.mediciones.all()}
        for clave in ('pruebas_aprobadas', 'avance_ejecucion', 'cumplimiento_sqa'):
            grafica['series'].setdefault(clave, []).append(valores.get(clave))
    detalle = corte.detalle.get('pendientes', {}) if corte else {}
    return render(request, 'metricas/dashboard.html', {
        'proyecto': proyecto, 'corte': corte, 'mediciones': corte.mediciones.all() if corte else [],
        'cortes': reversed(cortes), 'grafica': grafica, 'pendientes': detalle, 'etiquetas': ETIQUETAS,
        'total_pendientes': sum(len(v) for v in detalle.values())})


@require_POST
def crear_corte(request, proyecto_id):
    proyecto = get_object_or_404(Proyecto, pk=proyecto_id)
    texto = request.POST.get('fecha_corte', '').strip()
    fecha = None
    if texto:
        try:
            fecha = datetime.strptime(texto, '%Y-%m-%d').date()
        except ValueError:
            messages.error(request, 'La fecha de corte debe tener formato AAAA-MM-DD.')
            return redirect('metricas:dashboard', proyecto_id=proyecto.pk)
    corte = registrar_corte(proyecto, fecha)
    messages.success(request, f'Corte al {corte.fecha_corte:%d/%m/%Y} calculado y guardado.')
    return redirect(f"{proyecto.get_absolute_url()}?corte={corte.fecha_corte}")
