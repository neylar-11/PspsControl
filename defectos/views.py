from django.shortcuts import get_object_or_404

from config.utils import vista_formulario, vista_lista
from .forms import DefectoForm
from .models import Defecto


def lista(request, proyecto_id):
    return vista_lista(request, proyecto_id, Defecto, 'defectos/lista.html', 'descripcion')


def crear(request, proyecto_id):
    return vista_formulario(request, proyecto_id, DefectoForm, 'Registrar defecto', 'defectos:lista')


def editar(request, proyecto_id, pk):
    defecto = get_object_or_404(Defecto, pk=pk, proyecto_id=proyecto_id)
    return vista_formulario(request, proyecto_id, DefectoForm, f'Editar {defecto.codigo}', 'defectos:lista', defecto)
