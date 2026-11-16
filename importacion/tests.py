"""Pruebas de importación CSV: validación completa antes de guardar."""
from datetime import date

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from actividades.models import Actividad
from config.testing import caso, proyecto
from defectos.models import Defecto
from importacion import validacion
from pruebas.models import CasoPrueba, ResultadoPrueba

CAB_ACT = 'identificador,nombre,tipo,responsable,fecha_prevista,estado,fecha_terminada,evidencia\n'
OK1 = 'A-1,Revisión SRS,Revisión,Luis,2026-10-10,Terminada,2026-10-11,PR 4\n'
OK2 = 'A-2,Inspección,Inspección,Sebastián,2026-10-12,Planeada,,Acta 2\n'


class ImportacionTest(TestCase):
    def subir(self, p, tipo, texto, accion='importar', codificacion='utf-8'):
        archivo = SimpleUploadedFile('datos.csv', texto.encode(codificacion), content_type='text/csv')
        return self.client.post(reverse('importacion:importar', args=[p.pk]),
                                {'tipo': tipo, 'archivo': archivo, 'accion': accion})

    def test_plantillas_descargables_con_encabezados(self):
        p = proyecto()
        for tipo, cfg in validacion.TIPOS.items():
            r = self.client.get(reverse('importacion:plantilla', args=[p.pk, tipo]))
            self.assertEqual(r.status_code, 200)
            self.assertEqual(r.content.decode('utf-8-sig').strip().split(','), list(cfg['columnas']))

    def test_plantilla_desconocida_da_404(self):
        p = proyecto()
        self.assertEqual(self.client.get(reverse('importacion:plantilla', args=[p.pk, 'xx'])).status_code, 404)

    def test_importa_archivo_valido_y_recalcula(self):
        p = proyecto()
        self.subir(p, 'actividades', CAB_ACT + OK1 + OK2)
        self.assertEqual(Actividad.objects.filter(proyecto=p).count(), 2)
        self.assertEqual(p.cortes.count(), 1)

    def test_solo_validar_no_guarda(self):
        p = proyecto()
        self.subir(p, 'actividades', CAB_ACT + OK1, accion='validar')
        self.assertEqual(Actividad.objects.count(), 0)

    def test_un_error_impide_guardar_todo(self):
        p = proyecto()
        r = self.subir(p, 'actividades', CAB_ACT + OK1 + 'A-3,,Revisión,Luis,2026-10-10,Planeada,,x\n')
        self.assertEqual(Actividad.objects.count(), 0)
        self.assertEqual(r.context['errores'][0]['fila'], 3)
        self.assertEqual(r.context['errores'][0]['campo'], 'nombre')

    def test_campos_vacios_obligatorios(self):
        p = proyecto()
        _, errores = validacion.validar(p, 'actividades', (CAB_ACT + ',,,,,,,\n').encode())
        self.assertGreaterEqual(len(errores), 6)

    def test_evidencia_vacia_se_rechaza(self):
        p = proyecto()
        _, errores = validacion.validar(p, 'actividades', (CAB_ACT + 'A-1,N,Revisión,L,2026-10-10,Planeada,,\n').encode())
        self.assertEqual([e['campo'] for e in errores], ['evidencia'])

    def test_fecha_invalida(self):
        p = proyecto()
        _, errores = validacion.validar(p, 'actividades', (CAB_ACT + 'A-1,N,Revisión,L,32/10/2026,Planeada,,x\n').encode())
        self.assertEqual(errores[0]['campo'], 'fecha_prevista')
        _, errores = validacion.validar(p, 'actividades', (CAB_ACT + 'A-1,N,Revisión,L,2026-02-30,Planeada,,x\n').encode())
        self.assertEqual(errores[0]['campo'], 'fecha_prevista')

    def test_valor_no_permitido(self):
        p = proyecto()
        _, errores = validacion.validar(p, 'actividades', (CAB_ACT + 'A-1,N,Magia,L,2026-10-10,Planeada,,x\n').encode())
        self.assertEqual(errores[0]['campo'], 'tipo')
        self.assertIn('Opciones', errores[0]['mensaje'])

    def test_identificador_duplicado_en_el_archivo(self):
        p = proyecto()
        _, errores = validacion.validar(p, 'actividades', (CAB_ACT + OK1 + OK1).encode())
        self.assertEqual(errores[0]['fila'], 3)
        self.assertIn('duplicado', errores[0]['mensaje'])

    def test_importacion_repetida_se_rechaza(self):
        p = proyecto()
        self.subir(p, 'actividades', CAB_ACT + OK1)
        r = self.subir(p, 'actividades', CAB_ACT + OK1)
        self.assertEqual(Actividad.objects.count(), 1)
        self.assertIn('repetida', r.context['errores'][0]['mensaje'])

    def test_mismo_identificador_en_otro_proyecto_no_es_duplicado(self):
        p1, p2 = proyecto(), proyecto(nombre='Otro')
        self.subir(p1, 'actividades', CAB_ACT + OK1)
        self.subir(p2, 'actividades', CAB_ACT + OK1)
        self.assertEqual(Actividad.objects.count(), 2)

    def test_encabezado_incorrecto(self):
        p = proyecto()
        _, errores = validacion.validar(p, 'actividades', b'nombre,otra\nx,y\n')
        self.assertEqual(errores[0]['campo'], '(encabezado)')
        self.assertIn('Faltan columnas', errores[0]['mensaje'])

    def test_archivo_vacio_o_sin_registros(self):
        p = proyecto()
        self.assertTrue(validacion.validar(p, 'actividades', b'')[1])
        self.assertTrue(validacion.validar(p, 'actividades', CAB_ACT.encode())[1])

    def test_codificacion_invalida(self):
        p = proyecto()
        _, errores = validacion.validar(p, 'actividades', b'\x81')
        self.assertIn('UTF-8', errores[0]['mensaje'])

    def test_acepta_punto_y_coma_de_excel(self):
        p = proyecto()
        texto = (CAB_ACT + OK1).replace(',', ';')
        filas, errores = validacion.validar(p, 'actividades', texto.encode('utf-8-sig'))
        self.assertEqual((len(filas), errores), (1, []))

    def test_acepta_csv_en_cp1252_de_excel(self):
        p = proyecto()
        filas, errores = validacion.validar(p, 'actividades', (CAB_ACT + OK1 + OK2).encode('cp1252'))
        self.assertEqual((len(filas), errores), (2, []))
        self.assertEqual(filas[0]['nombre'], 'Revisión SRS')
        self.assertEqual(filas[1]['responsable'], 'Sebastián')

    def test_acepta_fechas_dd_mm_aaaa_de_excel(self):
        p = proyecto()
        fila_act = 'A-1,Revisión SRS,Revisión,Luis,10/10/2026,Terminada,11/10/2026,PR 4\n'
        filas, errores = validacion.validar(p, 'actividades', (CAB_ACT + fila_act).encode('utf-8'))
        self.assertEqual(errores, [])
        self.assertEqual(filas[0]['fecha_prevista'], date(2026, 10, 10))
        self.assertEqual(filas[0]['fecha_terminada'], date(2026, 10, 11))
        cab_def = 'identificador,descripcion,severidad,estado,fecha_reporte,responsable,fecha_cierre,verificado_por,evidencia\n'
        fila_def = 'D-1,Falla,Alta,Cerrado,11/10/2026 10:00,Dev,12/10/2026 14:30,Francisco,log\n'
        filas_d, errores_d = validacion.validar(p, 'defectos', (cab_def + fila_def).encode('utf-8'))
        self.assertEqual((len(filas_d), errores_d), (1, []))

    def test_ignora_columna_vacia_al_final_de_excel(self):
        p = proyecto()
        cab_extra = CAB_ACT.rstrip('\n') + ',\n'
        fila_extra = OK1.rstrip('\n') + ',\n'
        filas, errores = validacion.validar(p, 'actividades', (cab_extra + fila_extra).encode('utf-8'))
        self.assertEqual((len(filas), errores), (1, []))

    def test_casos_y_resultados(self):
        p = proyecto()
        self.subir(p, 'casos', 'identificador,nombre,version,pasos,resultado_esperado,responsable,fecha_prevista\n'
                               'CP-1,Login,v0.1,Entrar,Accede,Francisco,2026-10-10\n')
        self.assertEqual(CasoPrueba.objects.count(), 1)
        cab = 'identificador_caso,fecha_ejecucion,resultado,resultado_obtenido,ejecutor,evidencia\n'
        self.subir(p, 'resultados', cab + 'CP-1,2026-10-11,Aprobada,ok,Sebastián,cap.png\n')
        self.assertEqual(ResultadoPrueba.objects.count(), 1)
        r = self.subir(p, 'resultados', cab + 'CP-1,2026-10-11,Aprobada,ok,Sebastián,cap.png\n')
        self.assertEqual(ResultadoPrueba.objects.count(), 1)
        self.assertIn('repetida', r.context['errores'][0]['mensaje'])

    def test_resultado_de_caso_inexistente(self):
        p = proyecto()
        cab = 'identificador_caso,fecha_ejecucion,resultado,resultado_obtenido,ejecutor,evidencia\n'
        _, errores = validacion.validar(p, 'resultados', (cab + 'CP-9,2026-10-11,Aprobada,ok,QA,x\n').encode())
        self.assertIn('No existe un caso', errores[0]['mensaje'])

    def test_defectos_cerrados_requieren_cierre_y_verificador(self):
        p = proyecto()
        cab = 'identificador,descripcion,severidad,estado,fecha_reporte,responsable,fecha_cierre,verificado_por,evidencia\n'
        _, errores = validacion.validar(p, 'defectos', (cab + 'D-1,Falla,Alta,Cerrado,2026-10-11 10:00,Dev,,,log\n').encode())
        self.assertEqual({e['campo'] for e in errores}, {'fecha_cierre', 'verificado_por'})
        self.subir(p, 'defectos', cab + 'D-1,Falla,Crítica,Cerrado,2026-10-11 10:00,Dev,2026-10-12 10:00,Francisco,log\n')
        d = Defecto.objects.get()
        self.assertEqual(d.horas_resolucion, 24.0)

    def test_tipo_invalido_o_sin_archivo(self):
        p = proyecto()
        r = self.client.post(reverse('importacion:importar', args=[p.pk]), {'tipo': 'x'}, follow=True)
        self.assertContains(r, 'tipo de registro')
        r = self.client.post(reverse('importacion:importar', args=[p.pk]), {'tipo': 'actividades'}, follow=True)
        self.assertContains(r, 'Selecciona un archivo')
