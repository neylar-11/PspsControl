from django.shortcuts import get_object_or_404

from config.utils import vista_formulario, vista_lista
from .forms import ActividadForm
from .models import Actividad


def lista(request, proyecto_id):
    return vista_lista(request, proyecto_id, Actividad, 'actividades/lista.html', 'nombre')


def crear(request, proyecto_id):
    return vista_formulario(request, proyecto_id, ActividadForm, 'Nueva actividad SQA', 'actividades:lista')


def editar(request, proyecto_id, pk):
    actividad = get_object_or_404(Actividad, pk=pk, proyecto_id=proyecto_id)
    return vista_formulario(request, proyecto_id, ActividadForm, f'Editar {actividad.codigo}', 'actividades:lista', actividad)
