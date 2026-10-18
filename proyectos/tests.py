from datetime import date

from django.test import TestCase
from django.urls import reverse

from config.testing import proyecto
from proyectos.models import Proyecto


class ProyectosTest(TestCase):
    def datos(self, **kw):
        d = {'nombre': 'App A', 'descripcion': '', 'responsable': 'Alan', 'fecha_inicio': '2026-10-06',
             'fecha_fin': '', 'duracion_dias': 14, 'objetivo_resolucion_horas': 72}
        d.update(kw)
        return d

    def test_registrar_proyecto_calcula_fin_con_la_duracion(self):
        r = self.client.post(reverse('proyectos:crear'), self.datos())
        p = Proyecto.objects.get()
        self.assertEqual(p.fecha_fin, date(2026, 10, 20))
        self.assertRedirects(r, p.get_absolute_url(), fetch_redirect_response=False)

    def test_fin_anterior_al_inicio_se_rechaza(self):
        self.client.post(reverse('proyectos:crear'), self.datos(fecha_fin='2026-10-01'))
        self.assertEqual(Proyecto.objects.count(), 0)

    def test_campos_obligatorios(self):
        r = self.client.post(reverse('proyectos:crear'), self.datos(nombre='', responsable=''))
        self.assertEqual(Proyecto.objects.count(), 0)
        self.assertContains(r, 'obligatorio')

    def test_no_duplica_mismo_nombre_e_intervalo(self):
        self.client.post(reverse('proyectos:crear'), self.datos())
        self.client.post(reverse('proyectos:crear'), self.datos())
        self.assertEqual(Proyecto.objects.count(), 1)

    def test_nuevo_intervalo_conserva_los_anteriores(self):
        anterior = proyecto(nombre='App A')
        self.client.post(reverse('proyectos:crear'), self.datos(fecha_inicio='2026-10-20'))
        self.assertEqual(Proyecto.objects.filter(nombre='App A').count(), 2)
        self.assertTrue(Proyecto.objects.filter(pk=anterior.pk).exists())

    def test_formulario_de_nuevo_intervalo_precarga_datos(self):
        anterior = proyecto(nombre='App A')
        r = self.client.get(reverse('proyectos:crear') + f'?desde={anterior.pk}')
        self.assertContains(r, 'value="App A"')
        self.assertContains(r, 'value="2026-10-20"')

    def test_editar_proyecto(self):
        p = proyecto()
        self.client.post(reverse('proyectos:editar', args=[p.pk]), self.datos(nombre='Nuevo nombre', fecha_fin='2026-10-30'))
        p.refresh_from_db()
        self.assertEqual(p.nombre, 'Nuevo nombre')

    def test_lista_vacia_y_con_proyecto(self):
        self.assertContains(self.client.get(reverse('proyectos:lista')), 'Aún no hay proyectos')
        proyecto()
        self.assertContains(self.client.get(reverse('proyectos:lista')), 'Proyecto de prueba')

    def test_confirmar_registro_de_defectos(self):
        p = proyecto()
        self.client.post(reverse('proyectos:confirmar_defectos', args=[p.pk]), {'confirmado': '1'})
        p.refresh_from_db()
        self.assertTrue(p.registro_defectos_confirmado)
