"""Fábricas de datos para las pruebas."""
from datetime import date, datetime, timedelta

from django.utils import timezone

from actividades.models import Actividad
from defectos.models import Defecto
from proyectos.models import Proyecto
from pruebas.models import CasoPrueba, ResultadoPrueba

HOY = date(2026, 10, 20)


def dt(d, hora=9):
    return timezone.make_aware(datetime(d.year, d.month, d.day, hora, 0))


def proyecto(**kw):
    datos = dict(nombre='Proyecto de prueba', responsable='QA', fecha_inicio=date(2026, 10, 6),
                 fecha_fin=date(2026, 10, 20), duracion_dias=14, objetivo_resolucion_horas=72)
    datos.update(kw)
    return Proyecto.objects.create(**datos)


def actividad(p, prevista=date(2026, 10, 10), estado='Terminada', terminada=None, evidencia='PR #1', **kw):
    if estado == 'Terminada' and terminada is None:
        terminada = prevista
    return Actividad.objects.create(proyecto=p, nombre='Revisión', tipo='Revisión', responsable='Equipo',
                                    fecha_prevista=prevista, estado=estado, fecha_terminada=terminada,
                                    evidencia=evidencia, **kw)


def caso(p, prevista=date(2026, 10, 10), **kw):
    return CasoPrueba.objects.create(proyecto=p, nombre='Caso', version='v0.1', pasos='1. Abrir',
                                     resultado_esperado='Funciona', responsable='QA', fecha_prevista=prevista, **kw)


def resultado(c, fecha=date(2026, 10, 11), res='Aprobada'):
    return ResultadoPrueba.objects.create(caso=c, fecha_ejecucion=fecha, resultado=res, resultado_obtenido='ok',
                                          ejecutor='QA', evidencia='captura.png')


def defecto(p, severidad='Media', estado='Abierto', reporte=date(2026, 10, 11), horas=None, **kw):
    cierre = None
    if estado == 'Cerrado':
        cierre = dt(reporte) + timedelta(hours=horas if horas is not None else 24)
        kw.setdefault('verificado_por', 'QA')
    return Defecto.objects.create(proyecto=p, descripcion='Falla', severidad=severidad, estado=estado,
                                  fecha_reporte=dt(reporte), responsable='Dev', fecha_cierre=cierre,
                                  evidencia='log.txt', **kw)


def indicador(resultado_calculo, clave):
    return next(i for i in resultado_calculo['indicadores'] if i['clave'] == clave)
