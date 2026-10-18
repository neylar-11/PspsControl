from datetime import date

from django.test import TestCase
from django.urls import reverse

from config.testing import actividad, defecto, proyecto
from metricas.servicio import registrar_corte


class ReportesTest(TestCase):
    def test_reporte_sin_cortes(self):
        p = proyecto()
        self.assertContains(self.client.get(reverse('reportes:reporte', args=[p.pk])), 'Sin cortes para reportar')

    def test_reporte_a_fecha_de_corte_historico_no_cambia(self):
        p = proyecto()
        actividad(p, prevista=date(2026, 10, 10))
        registrar_corte(p, date(2026, 10, 15))
        defecto(p, severidad='Crítica', reporte=date(2026, 10, 16))
        registrar_corte(p, date(2026, 10, 20))
        url = reverse('reportes:reporte', args=[p.pk])
        antiguo = self.client.get(url + '?corte=2026-10-15').content.decode()
        nuevo = self.client.get(url + '?corte=2026-10-20').content.decode()
        self.assertNotIn('Defecto <strong>DEF-001', antiguo)
        self.assertIn('Defecto <strong>DEF-001', nuevo)

    def test_fecha_de_corte_inexistente_muestra_el_ultimo(self):
        p = proyecto()
        registrar_corte(p, date(2026, 10, 15))
        r = self.client.get(reverse('reportes:reporte', args=[p.pk]) + '?corte=basura')
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, '15/10/2026')

    def test_proyecto_inexistente(self):
        self.assertEqual(self.client.get(reverse('reportes:reporte', args=[999])).status_code, 404)
