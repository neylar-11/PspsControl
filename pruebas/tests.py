from datetime import date

from django.test import TestCase
from django.urls import reverse

from config.testing import caso, proyecto, resultado
from pruebas.models import CasoPrueba, ResultadoPrueba


class PruebasTest(TestCase):
    def test_crear_caso_con_version_y_resultado_esperado(self):
        p = proyecto()
        self.client.post(reverse('pruebas:crear', args=[p.pk]), {
            'codigo': '', 'nombre': 'Login válido', 'version': 'v0.2', 'pasos': '1. Entrar', 'resultado_esperado': 'Accede',
            'responsable': 'Francisco', 'fecha_prevista': '2026-10-15'})
        c = CasoPrueba.objects.get()
        self.assertEqual((c.codigo, c.version), ('CP-001', 'v0.2'))

    def test_caso_sin_resultado_esperado_se_rechaza(self):
        p = proyecto()
        self.client.post(reverse('pruebas:crear', args=[p.pk]), {
            'nombre': 'X', 'version': 'v1', 'pasos': 'p', 'resultado_esperado': '', 'responsable': 'a',
            'fecha_prevista': '2026-10-15'})
        self.assertEqual(CasoPrueba.objects.count(), 0)

    def test_registrar_resultado_exige_evidencia(self):
        p = proyecto()
        c = caso(p)
        url = reverse('pruebas:resultado', args=[p.pk, c.pk])
        base = {'fecha_ejecucion': '2026-10-16', 'resultado': 'Aprobada', 'resultado_obtenido': 'ok', 'ejecutor': 'QA'}
        self.client.post(url, {**base, 'evidencia': ''})
        self.assertEqual(ResultadoPrueba.objects.count(), 0)
        self.client.post(url, {**base, 'evidencia': 'captura.png'})
        self.assertEqual(ResultadoPrueba.objects.count(), 1)

    def test_lista_muestra_ultimo_resultado_y_filtra(self):
        p = proyecto()
        c1, c2 = caso(p), caso(p)
        resultado(c1, date(2026, 10, 11), 'Fallida')
        resultado(c1, date(2026, 10, 12), 'Aprobada')
        url = reverse('pruebas:lista', args=[p.pk])
        r = self.client.get(url)
        self.assertEqual({f['etiqueta'] for f in r.context['filas']}, {'Aprobada', 'Sin ejecutar'})
        self.assertEqual(len(self.client.get(url + '?estado=Fallida').context['filas']), 0)
        self.assertEqual(len(self.client.get(url + '?estado=Sin ejecutar').context['filas']), 1)
