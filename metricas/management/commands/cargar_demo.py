"""Carga un proyecto de EJEMPLO (datos ficticios, rotulados DEMO) para ensayar la demostración.

No son mediciones reales del equipo: no se deben presentar como avance histórico.
"""
from datetime import date, datetime, timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from actividades.models import Actividad
from defectos.models import Defecto
from metricas.servicio import registrar_corte
from proyectos.models import Proyecto
from pruebas.models import CasoPrueba, ResultadoPrueba


def dt(d, h=9):
    return timezone.make_aware(datetime(d.year, d.month, d.day, h))


class Command(BaseCommand):
    help = 'Crea el proyecto de ejemplo "PSPS Academy (DEMO)" con datos ficticios.'

    def handle(self, *args, **opciones):
        if Proyecto.objects.filter(nombre='PSPS Academy (DEMO)').exists():
            self.stdout.write('Los datos DEMO ya existen.')
            return
        p = Proyecto.objects.create(nombre='PSPS Academy (DEMO)', responsable='Equipo PSPS',
                                    descripcion='Datos de ejemplo, no son mediciones reales.',
                                    fecha_inicio=date(2026, 10, 6), fecha_fin=date(2026, 10, 20), duracion_dias=14)
        for cod, nom, prev, est, ter in [
                ('ACT-001', 'Revisión de requisitos', date(2026, 10, 8), 'Terminada', date(2026, 10, 8)),
                ('ACT-002', 'Inspección de wireframes', date(2026, 10, 12), 'Terminada', date(2026, 10, 13)),
                ('ACT-003', 'Revisión de código del módulo 1', date(2026, 10, 16), 'Terminada', date(2026, 10, 17)),
                ('ACT-004', 'Revisión de código del módulo 2', date(2026, 10, 19), 'En curso', None),
                ('ACT-005', 'Auditoría de entrega', date(2026, 10, 25), 'Planeada', None)]:
            Actividad.objects.create(proyecto=p, codigo=cod, nombre=nom, tipo='Revisión', responsable='QA',
                                     fecha_prevista=prev, estado=est, fecha_terminada=ter,
                                     evidencia='DEMO: registro simulado')
        resultados = [('CP-001', date(2026, 10, 10), date(2026, 10, 11), 'Aprobada'),
                      ('CP-002', date(2026, 10, 12), date(2026, 10, 13), 'Aprobada'),
                      ('CP-003', date(2026, 10, 14), date(2026, 10, 15), 'Fallida'),
                      ('CP-004', date(2026, 10, 16), date(2026, 10, 17), 'Aprobada'),
                      ('CP-005', date(2026, 10, 18), None, None)]
        for cod, prev, ejec, res in resultados:
            c = CasoPrueba.objects.create(proyecto=p, codigo=cod, nombre=f'Caso de prueba {cod[-3:]}', version='v0.1',
                                          pasos='Pasos de ejemplo', resultado_esperado='Resultado esperado de ejemplo',
                                          responsable='QA', fecha_prevista=prev)
            if ejec:
                ResultadoPrueba.objects.create(caso=c, fecha_ejecucion=ejec, resultado=res, ejecutor='QA',
                                               resultado_obtenido='DEMO', evidencia='DEMO: captura simulada')
        Defecto.objects.create(proyecto=p, codigo='DEF-001', descripcion='Mensaje de validación ambiguo (DEMO)',
                               severidad='Media', estado='Cerrado', fecha_reporte=dt(date(2026, 10, 15)),
                               fecha_cierre=dt(date(2026, 10, 15)) + timedelta(hours=40), verificado_por='QA',
                               responsable='Desarrollo', evidencia='DEMO: log simulado')
        Defecto.objects.create(proyecto=p, codigo='DEF-002', descripcion='Cálculo incorrecto en el borde del semáforo (DEMO)',
                               severidad='Alta', estado='En corrección', fecha_reporte=dt(date(2026, 10, 17)),
                               responsable='Desarrollo', evidencia='DEMO: captura simulada')
        for fecha in (date(2026, 10, 13), date(2026, 10, 16), date(2026, 10, 20)):
            registrar_corte(p, fecha)
        self.stdout.write(self.style.SUCCESS('Proyecto DEMO creado con 3 cortes.'))
