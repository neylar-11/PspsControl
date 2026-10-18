from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from metricas.servicio import ultimo_corte
from .forms import ProyectoForm
from .models import Proyecto


def lista(request):
    proyectos = [{'proyecto': p, 'corte': ultimo_corte(p)} for p in Proyecto.objects.all()]
    return render(request, 'proyectos/lista.html', {'items': proyectos})


def crear(request):
    inicial = {}
    origen = request.GET.get('desde')
    if origen and origen.isdigit():
        previo = Proyecto.objects.filter(pk=origen).first()
        if previo:  # nuevo intervalo del mismo proyecto, sin tocar los anteriores
            inicial = {'nombre': previo.nombre, 'descripcion': previo.descripcion, 'responsable': previo.responsable,
                       'fecha_inicio': previo.fecha_fin, 'duracion_dias': previo.duracion_dias,
                       'objetivo_resolucion_horas': previo.objetivo_resolucion_horas}
    form = ProyectoForm(request.POST or None, initial=inicial)
    if request.method == 'POST' and form.is_valid():
        proyecto = form.save()
        messages.success(request, 'Proyecto registrado.')
        return redirect(proyecto)
    return render(request, 'form.html', {'form': form, 'titulo': 'Nuevo proyecto / intervalo', 'volver': 'proyectos:lista'})


def editar(request, pk):
    proyecto = get_object_or_404(Proyecto, pk=pk)
    form = ProyectoForm(request.POST or None, instance=proyecto)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Proyecto actualizado.')
        return redirect(proyecto)
    return render(request, 'form.html', {'form': form, 'titulo': f'Editar {proyecto.nombre}', 'volver': 'proyectos:lista'})


@require_POST
def confirmar_defectos(request, pk):
    proyecto = get_object_or_404(Proyecto, pk=pk)
    proyecto.registro_defectos_confirmado = request.POST.get('confirmado') == '1'
    proyecto.save(update_fields=['registro_defectos_confirmado'])
    from metricas.servicio import registrar_corte
    registrar_corte(proyecto)
    messages.success(request, 'Confirmación del registro de defectos actualizada.')
    return redirect(proyecto)
