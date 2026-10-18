from django.contrib import messages
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, render

from metricas.servicio import registrar_corte
from proyectos.models import Proyecto
from . import validacion


def importar(request, proyecto_id):
    proyecto = get_object_or_404(Proyecto, pk=proyecto_id)
    contexto = {'proyecto': proyecto, 'tipos': validacion.TIPOS, 'errores': None, 'tipo_sel': 'actividades'}
    if request.method == 'POST':
        tipo = request.POST.get('tipo', '')
        archivo = request.FILES.get('archivo')
        contexto['tipo_sel'] = tipo
        if tipo not in validacion.TIPOS:
            messages.error(request, 'Elige un tipo de registro válido.')
        elif archivo is None:
            messages.error(request, 'Selecciona un archivo CSV.')
        elif archivo.size > 2 * 1024 * 1024:
            messages.error(request, 'El archivo supera 2 MB.')
        else:
            filas, errores = validacion.validar(proyecto, tipo, archivo.read())
            if errores:
                contexto['errores'] = errores
                messages.error(request, f'Se encontraron {len(errores)} error(es). No se importó ningún registro.')
            elif request.POST.get('accion') == 'validar':
                messages.success(request, f'Validación correcta: {len(filas)} registro(s) listos para importar.')
            else:
                total = validacion.guardar(proyecto, tipo, filas)
                registrar_corte(proyecto)
                messages.success(request, f'Se importaron {total} registro(s). Los indicadores se recalcularon.')
    return render(request, 'importacion/importar.html', contexto)


def plantilla(request, proyecto_id, tipo):
    if tipo not in validacion.TIPOS:
        raise Http404
    respuesta = HttpResponse(validacion.plantilla_csv(tipo), content_type='text/csv; charset=utf-8')
    respuesta['Content-Disposition'] = f'attachment; filename="plantilla_{tipo}.csv"'
    return respuesta
