"""Pruebas del servicio de métricas: cálculos, límites de semáforo, corte y estado general."""
from datetime import date

from django.test import TestCase
from django.urls import reverse

from config.testing import HOY, actividad, caso, defecto, indicador, proyecto, resultado
from metricas import servicio
from metricas.models import Corte


class SemaforosTest(TestCase):
    def test_limites_exactos_porcentaje_pruebas(self):
        self.assertEqual(servicio.semaforo_porcentaje(95, 95, 80), 'verde')
        self.assertEqual(servicio.semaforo_porcentaje(94.9, 95, 80), 'amarillo')
        self.assertEqual(servicio.semaforo_porcentaje(80, 95, 80), 'amarillo')
        self.assertEqual(servicio.semaforo_porcentaje(79.9, 95, 80), 'rojo')

    def test_limites_exactos_avance_y_sqa(self):
        for verde, amarillo in ((90, 70),):
            self.assertEqual(servicio.semaforo_porcentaje(90, verde, amarillo), 'verde')
            self.assertEqual(servicio.semaforo_porcentaje(89.9, verde, amarillo), 'amarillo')
            self.assertEqual(servicio.semaforo_porcentaje(70, verde, amarillo), 'amarillo')
            self.assertEqual(servicio.semaforo_porcentaje(69.9, verde, amarillo), 'rojo')

    def test_limites_exactos_tiempo_resolucion(self):
        self.assertEqual(servicio.semaforo_tiempo(72, 72), 'verde')
        self.assertEqual(servicio.semaforo_tiempo(72.1, 72), 'amarillo')
        self.assertEqual(servicio.semaforo_tiempo(144, 72), 'amarillo')
        self.assertEqual(servicio.semaforo_tiempo(144.1, 72), 'rojo')


class EstadoGeneralTest(TestCase):
    def estado(self, *estados):
        return servicio.estado_general([{'estado': e} for e in estados])[0]

    def test_prioridad_rojo_gris_amarillo_verde(self):
        self.assertEqual(self.estado('verde', 'amarillo', 'gris', 'rojo'), 'rojo')
        self.assertEqual(self.estado('verde', 'amarillo', 'gris'), 'gris')
        self.assertEqual(self.estado('verde', 'amarillo'), 'amarillo')
        self.assertEqual(self.estado('verde', 'verde'), 'verde')

    def test_no_aplicables_se_excluyen(self):
        self.assertEqual(self.estado('verde', 'no_aplica'), 'verde')
        self.assertEqual(self.estado('no_aplica', 'no_aplica'), 'gris')


class IndicadoresTest(TestCase):
    def test_proyecto_vacio_no_inventa_resultados(self):
        r = servicio.calcular(proyecto(), HOY)
        for clave in ('pruebas_aprobadas', 'avance_ejecucion', 'defectos_criticos', 'cumplimiento_sqa', 'tiempo_resolucion'):
            self.assertEqual(indicador(r, clave)['estado'], 'gris', clave)
            self.assertIsNone(indicador(r, clave)['valor'], clave)
        self.assertEqual(r['estado_general'], 'gris')

    def test_division_entre_cero_no_es_cero_por_ciento(self):
        p = proyecto()
        caso(p)  # previsto pero sin ejecutar
        r = servicio.calcular(p, HOY)
        self.assertEqual(indicador(r, 'pruebas_aprobadas')['estado'], 'gris')
        self.assertEqual(indicador(r, 'avance_ejecucion')['valor'], 0.0)
        self.assertEqual(indicador(r, 'avance_ejecucion')['estado'], 'rojo')

    def test_pruebas_aprobadas_porcentaje(self):
        p = proyecto()
        for res in ['Aprobada'] * 19 + ['Fallida']:
            resultado(caso(p), res=res)
        i = indicador(servicio.calcular(p, HOY), 'pruebas_aprobadas')
        self.assertEqual((i['valor'], i['estado']), (95.0, 'verde'))

    def test_ultimo_resultado_por_caso(self):
        p = proyecto()
        c = caso(p)
        resultado(c, date(2026, 10, 11), 'Fallida')
        resultado(c, date(2026, 10, 15), 'Aprobada')
        self.assertEqual(indicador(servicio.calcular(p, HOY), 'pruebas_aprobadas')['valor'], 100.0)
        self.assertEqual(indicador(servicio.calcular(p, date(2026, 10, 12)), 'pruebas_aprobadas')['valor'], 0.0)

    def test_corte_excluye_registros_posteriores(self):
        p = proyecto()
        c = caso(p, prevista=date(2026, 10, 10))
        resultado(c, date(2026, 10, 18))
        antes = servicio.calcular(p, date(2026, 10, 15))
        self.assertEqual(indicador(antes, 'pruebas_aprobadas')['estado'], 'gris')
        self.assertEqual(indicador(antes, 'avance_ejecucion')['valor'], 0.0)
        despues = servicio.calcular(p, date(2026, 10, 18))
        self.assertEqual(indicador(despues, 'avance_ejecucion')['valor'], 100.0)

    def test_avance_no_aplica_si_nada_previsto_al_corte(self):
        p = proyecto()
        caso(p, prevista=date(2026, 12, 1))
        i = indicador(servicio.calcular(p, HOY), 'avance_ejecucion')
        self.assertEqual(i['estado'], 'no_aplica')
        self.assertTrue(i['motivo'])

    def test_cumplimiento_sqa_mismo_conjunto_exigible(self):
        p = proyecto()
        actividad(p, prevista=date(2026, 10, 10))                       # exigible y terminada
        actividad(p, prevista=date(2026, 10, 12), estado='En curso')    # exigible, pendiente
        actividad(p, prevista=date(2026, 11, 30))                       # NO exigible aunque esté terminada
        i = indicador(servicio.calcular(p, HOY), 'cumplimiento_sqa')
        self.assertEqual((i['numerador'], i['denominador'], i['valor']), (1, 2, 50.0))
        self.assertEqual(i['estado'], 'rojo')

    def test_actividad_terminada_despues_del_corte_es_pendiente(self):
        p = proyecto()
        actividad(p, prevista=date(2026, 10, 10), terminada=date(2026, 10, 19))
        self.assertEqual(indicador(servicio.calcular(p, date(2026, 10, 15)), 'cumplimiento_sqa')['valor'], 0.0)
        self.assertEqual(indicador(servicio.calcular(p, date(2026, 10, 19)), 'cumplimiento_sqa')['valor'], 100.0)

    def test_sin_defectos_requiere_confirmacion_para_reportar_cero(self):
        p = proyecto()
        self.assertEqual(indicador(servicio.calcular(p, HOY), 'defectos_criticos')['estado'], 'gris')
        p.registro_defectos_confirmado = True
        p.save()
        i = indicador(servicio.calcular(p, HOY), 'defectos_criticos')
        self.assertEqual((i['valor'], i['estado']), (0.0, 'verde'))
        self.assertEqual(indicador(servicio.calcular(p, HOY), 'tiempo_resolucion')['estado'], 'no_aplica')

    def test_defecto_critico_abierto_es_rojo_y_cerrar_lo_corrige(self):
        p = proyecto()
        d = defecto(p, severidad='Crítica')
        self.assertEqual(indicador(servicio.calcular(p, HOY), 'defectos_criticos')['estado'], 'rojo')
        self.assertEqual(servicio.calcular(p, HOY)['estado_general'], 'rojo')
        d.estado, d.fecha_cierre, d.verificado_por = 'Cerrado', defecto_cierre(d, 5), 'QA'
        d.save()
        self.assertEqual(indicador(servicio.calcular(p, HOY), 'defectos_criticos')['estado'], 'verde')

    def test_critico_cerrado_despues_del_corte_cuenta_como_abierto(self):
        p = proyecto()
        defecto(p, severidad='Crítica', estado='Cerrado', reporte=date(2026, 10, 11), horas=24 * 5)
        self.assertEqual(indicador(servicio.calcular(p, date(2026, 10, 13)), 'defectos_criticos')['valor'], 1.0)
        self.assertEqual(indicador(servicio.calcular(p, date(2026, 10, 20)), 'defectos_criticos')['valor'], 0.0)

    def test_tiempo_promedio_de_resolucion(self):
        p = proyecto()
        defecto(p, estado='Cerrado', horas=24)
        defecto(p, estado='Cerrado', horas=48)
        defecto(p, estado='Abierto')   # no entra al promedio
        i = indicador(servicio.calcular(p, HOY), 'tiempo_resolucion')
        self.assertEqual((i['valor'], i['estado']), (36.0, 'verde'))

    def test_tiempo_promedio_usa_T_del_proyecto(self):
        p = proyecto(objetivo_resolucion_horas=10)
        defecto(p, estado='Cerrado', horas=15)
        self.assertEqual(indicador(servicio.calcular(p, HOY), 'tiempo_resolucion')['estado'], 'amarillo')

    def test_defectos_sin_cierres_no_evalua_tiempo(self):
        p = proyecto()
        defecto(p)
        self.assertEqual(indicador(servicio.calcular(p, HOY), 'tiempo_resolucion')['estado'], 'gris')

    def test_proyecto_todo_verde(self):
        p = proyecto(registro_defectos_confirmado=True)
        resultado(caso(p))
        actividad(p)
        r = servicio.calcular(p, HOY)
        self.assertEqual(r['estado_general'], 'verde')


def defecto_cierre(d, horas):
    from datetime import timedelta
    return d.fecha_reporte + timedelta(hours=horas)


class CorteGuardadoTest(TestCase):
    def test_guarda_umbrales_y_conserva_historial(self):
        p = proyecto()
        actividad(p, prevista=date(2026, 10, 10))
        c1 = servicio.registrar_corte(p, date(2026, 10, 15))
        antes = {m.clave: (m.valor, m.estado) for m in c1.mediciones.all()}
        actividad(p, prevista=date(2026, 10, 11), estado='Planeada')   # cambia el panorama después
        servicio.registrar_corte(p, date(2026, 10, 20))
        c1.refresh_from_db()
        self.assertEqual(antes, {m.clave: (m.valor, m.estado) for m in c1.mediciones.all()})
        self.assertEqual(c1.umbrales['tiempo_resolucion_T_horas'], 72)
        self.assertEqual(p.cortes.count(), 2)

    def test_mismo_dia_reemplaza_solo_ese_corte(self):
        p = proyecto()
        servicio.registrar_corte(p, date(2026, 10, 15))
        servicio.registrar_corte(p, date(2026, 10, 15))
        self.assertEqual(Corte.objects.filter(proyecto=p).count(), 1)
        self.assertEqual(Corte.objects.get(proyecto=p).mediciones.count(), 5)

    def test_guardar_registro_recalcula_el_corte_del_dia(self):
        p = proyecto()
        self.client.post(reverse('actividades:crear', args=[p.pk]), {
            'nombre': 'Revisión SRS', 'tipo': 'Revisión', 'responsable': 'Francisco', 'fecha_prevista': '2026-10-01',
            'estado': 'Terminada', 'evidencia': 'PR #3'})
        corte = p.cortes.get()
        self.assertEqual(next(m for m in corte.mediciones.all() if m.clave == 'cumplimiento_sqa').valor, 100.0)


class DashboardYReporteTest(TestCase):
    def test_mismos_valores_en_dashboard_y_reporte(self):
        p = proyecto(registro_defectos_confirmado=True)
        c = caso(p)
        resultado(c)
        actividad(p)
        servicio.registrar_corte(p, HOY)
        for url in (reverse('metricas:dashboard', args=[p.pk]), reverse('reportes:reporte', args=[p.pk])):
            html = self.client.get(url + '?corte=2026-10-20').content.decode()
            self.assertIn('100', html)
            self.assertIn('Verde', html)
            self.assertIn('Pruebas aprobadas', html)

    def test_reporte_conserva_umbrales_y_pendientes(self):
        p = proyecto()
        actividad(p, prevista=date(2026, 10, 10), estado='En curso')
        servicio.registrar_corte(p, HOY)
        html = self.client.get(reverse('reportes:reporte', args=[p.pk])).content.decode()
        self.assertIn('Verde ≥ 90%', html)
        self.assertIn('En curso', html)

    def test_dashboard_sin_cortes(self):
        p = proyecto()
        r = self.client.get(reverse('metricas:dashboard', args=[p.pk]))
        self.assertContains(r, 'Todavía no hay mediciones')

    def test_crear_corte_con_fecha_invalida(self):
        p = proyecto()
        r = self.client.post(reverse('metricas:crear_corte', args=[p.pk]), {'fecha_corte': '31/12/2026'}, follow=True)
        self.assertContains(r, 'AAAA-MM-DD')
        self.assertEqual(p.cortes.count(), 0)
