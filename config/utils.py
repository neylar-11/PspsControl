"""Utilidades comunes de la capa de datos y vistas."""
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render

from proyectos.models import Proyecto


def asignar_codigo(instancia, prefijo, filtro_extra=None):
    """Asigna un identificador legible (ACT-001, DEF-002…) si no se indicó uno."""
    if instancia.codigo:
        return
    existentes = type(instancia).objects.filter(**(filtro_extra or {'proyecto': instancia.proyecto}))
    n = existentes.count() + 1
    while existentes.filter(codigo=f'{prefijo}-{n:03d}').exists():
        n += 1
    instancia.codigo = f'{prefijo}-{n:03d}'


def vista_lista(request, proyecto_id, modelo, plantilla, texto_busqueda, extra=None):
    """Lista filtrable por estado y texto (patrón común de actividades, pruebas y defectos)."""
    proyecto = get_object_or_404(Proyecto, pk=proyecto_id)
    registros = modelo.objects.filter(proyecto=proyecto)
    estado, q = request.GET.get('estado', ''), request.GET.get('q', '').strip()
    if estado:
        registros = registros.filter(estado=estado)
    if q:
        registros = registros.filter(**{texto_busqueda + '__icontains': q})
    contexto = {'proyecto': proyecto, 'registros': registros, 'estado': estado, 'q': q,
                'estados': [e[0] for e in modelo.ESTADOS]}
    contexto.update(extra(registros) if extra else {})
    return render(request, plantilla, contexto)


def vista_formulario(request, proyecto_id, form_class, titulo, destino, instancia=None, **kw):
    """Alta o edición con recálculo automático del corte del día al guardar."""
    from metricas.servicio import registrar_corte
    proyecto = get_object_or_404(Proyecto, pk=proyecto_id)
    form = form_class(request.POST or None, instance=instancia, proyecto=proyecto, **kw)
    if request.method == 'POST' and form.is_valid():
        form.save()
        registrar_corte(proyecto)
        messages.success(request, 'Registro guardado. Los indicadores se recalcularon.')
        return redirect(destino, proyecto_id=proyecto.pk)
    return render(request, 'form.html', {'form': form, 'titulo': titulo, 'proyecto': proyecto,
                                         'volver': destino, 'volver_args': [proyecto.pk]})
