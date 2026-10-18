from django.test import TestCase
from django.urls import reverse

from actividades.models import Actividad
from config.testing import actividad, proyecto


class ActividadesTest(TestCase):
    def datos(self, **kw):
        d = {'codigo': '', 'nombre': 'Inspección de wireframes', 'tipo': 'Inspección', 'responsable': 'Sebastián',
             'fecha_prevista': '2026-10-12', 'estado': 'Planeada', 'fecha_terminada': '', 'evidencia': 'Acta 1'}
        d.update(kw)
        return d

    def test_crear_actividad_asigna_identificador(self):
        p = proyecto()
        self.client.post(reverse('actividades:crear', args=[p.pk]), self.datos())
        self.client.post(reverse('actividades:crear', args=[p.pk]), self.datos(nombre='Otra'))
        self.assertEqual(list(Actividad.objects.values_list('codigo', flat=True)), ['ACT-001', 'ACT-002'])

    def test_evidencia_obligatoria(self):
        p = proyecto()
        r = self.client.post(reverse('actividades:crear', args=[p.pk]), self.datos(evidencia='   '))
        self.assertEqual(Actividad.objects.count(), 0)
        self.assertContains(r, 'obligatorio')

    def test_terminada_sin_fecha_usa_hoy_y_otro_estado_la_limpia(self):
        p = proyecto()
        a = actividad(p, estado='En curso')
        self.client.post(reverse('actividades:editar', args=[p.pk, a.pk]), self.datos(estado='Terminada'))
        a.refresh_from_db()
        self.assertIsNotNone(a.fecha_terminada)
        self.client.post(reverse('actividades:editar', args=[p.pk, a.pk]), self.datos(estado='En curso'))
        a.refresh_from_db()
        self.assertIsNone(a.fecha_terminada)

    def test_identificador_repetido_en_el_proyecto_se_rechaza(self):
        p = proyecto()
        self.client.post(reverse('actividades:crear', args=[p.pk]), self.datos(codigo='A-1'))
        self.client.post(reverse('actividades:crear', args=[p.pk]), self.datos(codigo='A-1'))
        self.assertEqual(Actividad.objects.count(), 1)

    def test_mismo_identificador_en_otro_proyecto_es_valido(self):
        p1, p2 = proyecto(), proyecto(nombre='Otro')
        self.client.post(reverse('actividades:crear', args=[p1.pk]), self.datos(codigo='A-1'))
        self.client.post(reverse('actividades:crear', args=[p2.pk]), self.datos(codigo='A-1'))
        self.assertEqual(Actividad.objects.count(), 2)

    def test_filtrar_por_estado_y_texto(self):
        p = proyecto()
        actividad(p, estado='En curso')
        actividad(p, estado='Terminada')
        url = reverse('actividades:lista', args=[p.pk])
        self.assertEqual(len(self.client.get(url + '?estado=En curso').context['registros']), 1)
        self.assertEqual(len(self.client.get(url + '?q=zzz').context['registros']), 0)

    def test_no_se_edita_actividad_de_otro_proyecto(self):
        p1, p2 = proyecto(), proyecto(nombre='Otro')
        a = actividad(p1)
        self.assertEqual(self.client.get(reverse('actividades:editar', args=[p2.pk, a.pk])).status_code, 404)
