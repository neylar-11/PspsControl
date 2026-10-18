from django.test import TestCase
from django.urls import reverse

from config.testing import defecto, proyecto
from defectos.models import Defecto


class DefectosTest(TestCase):
    def datos(self, **kw):
        d = {'codigo': '', 'descripcion': 'No guarda el formulario', 'severidad': 'Alta', 'estado': 'Abierto',
             'fecha_reporte': '2026-10-12T10:00', 'responsable': 'Pablo', 'fecha_cierre': '', 'verificado_por': '',
             'evidencia': 'captura.png'}
        d.update(kw)
        return d

    def test_registrar_defecto(self):
        p = proyecto()
        self.client.post(reverse('defectos:crear', args=[p.pk]), self.datos())
        d = Defecto.objects.get()
        self.assertEqual((d.codigo, d.severidad), ('DEF-001', 'Alta'))

    def test_evidencia_obligatoria(self):
        p = proyecto()
        self.client.post(reverse('defectos:crear', args=[p.pk]), self.datos(evidencia=''))
        self.assertEqual(Defecto.objects.count(), 0)

    def test_cerrar_exige_fecha_y_verificador(self):
        p = proyecto()
        r = self.client.post(reverse('defectos:crear', args=[p.pk]), self.datos(estado='Cerrado'))
        self.assertEqual(Defecto.objects.count(), 0)
        self.assertContains(r, 'cierre verificado')
        self.client.post(reverse('defectos:crear', args=[p.pk]),
                         self.datos(estado='Cerrado', fecha_cierre='2026-10-13T10:00', verificado_por='Francisco'))
        self.assertEqual(Defecto.objects.get().horas_resolucion, 24.0)

    def test_cierre_no_puede_ser_anterior_al_reporte(self):
        p = proyecto()
        self.client.post(reverse('defectos:crear', args=[p.pk]),
                         self.datos(estado='Cerrado', fecha_cierre='2026-10-11T10:00', verificado_por='F'))
        self.assertEqual(Defecto.objects.count(), 0)

    def test_reabrir_limpia_el_cierre(self):
        p = proyecto()
        d = defecto(p, estado='Cerrado')
        self.client.post(reverse('defectos:editar', args=[p.pk, d.pk]), self.datos(estado='Abierto'))
        d.refresh_from_db()
        self.assertIsNone(d.fecha_cierre)

    def test_filtro_por_severidad_de_texto(self):
        p = proyecto()
        defecto(p)
        url = reverse('defectos:lista', args=[p.pk])
        self.assertEqual(len(self.client.get(url + '?q=Falla').context['registros']), 1)
        self.assertEqual(len(self.client.get(url + '?estado=Cerrado').context['registros']), 0)
