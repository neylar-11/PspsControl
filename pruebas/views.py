from django.shortcuts import get_object_or_404, render

from config.utils import vista_formulario
from proyectos.models import Proyecto
from .forms import CasoForm, ResultadoForm
from .models import CasoPrueba


def lista(request, proyecto_id):
    proyecto = get_object_or_404(Proyecto, pk=proyecto_id)
    q, estado = request.GET.get('q', '').strip(), request.GET.get('estado', '')
    casos = CasoPrueba.objects.filter(proyecto=proyecto).prefetch_related('resultados')
    if q:
        casos = casos.filter(nombre__icontains=q)
    filas = []
    for caso in casos:
        ultimo = caso.ultimo_resultado()
        etiqueta = ultimo.resultado if ultimo else 'Sin ejecutar'
        if not estado or estado == etiqueta:
            filas.append({'caso': caso, 'ultimo': ultimo, 'etiqueta': etiqueta})
    return render(request, 'pruebas/lista.html', {'proyecto': proyecto, 'filas': filas, 'q': q, 'estado': estado,
                                                  'estados': ['Aprobada', 'Fallida', 'Sin ejecutar']})


def crear(request, proyecto_id):
    return vista_formulario(request, proyecto_id, CasoForm, 'Nuevo caso de prueba', 'pruebas:lista')


def editar(request, proyecto_id, pk):
    caso = get_object_or_404(CasoPrueba, pk=pk, proyecto_id=proyecto_id)
    return vista_formulario(request, proyecto_id, CasoForm, f'Editar {caso.codigo}', 'pruebas:lista', caso)


def resultado(request, proyecto_id, pk):
    caso = get_object_or_404(CasoPrueba, pk=pk, proyecto_id=proyecto_id)
    return vista_formulario(request, proyecto_id, ResultadoForm, f'Resultado de {caso.codigo}', 'pruebas:lista', caso=caso)
