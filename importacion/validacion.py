"""Validación e importación de CSV (capa de dominio).

Regla del proyecto: se valida TODO el archivo antes de guardar; si hay un solo error no se escribe nada.
"""
import csv
import io
from datetime import datetime

from django.db import transaction
from django.utils import timezone

from actividades.models import Actividad
from defectos.models import Defecto
from pruebas.models import CasoPrueba, ResultadoPrueba

MAX_FILAS = 2000

# columna → (obligatoria, tipo) ; tipo: texto | fecha | fechahora | ('opciones', [...])
TIPOS = {
    'actividades': {
        'titulo': 'Actividades SQA', 'id': 'identificador',
        'columnas': {
            'identificador': (True, 'texto'), 'nombre': (True, 'texto'),
            'tipo': (True, ('opciones', [t[0] for t in Actividad.TIPOS])), 'responsable': (True, 'texto'),
            'fecha_prevista': (True, 'fecha'), 'estado': (True, ('opciones', [e[0] for e in Actividad.ESTADOS])),
            'fecha_terminada': (False, 'fecha'), 'evidencia': (True, 'texto')}},
    'casos': {
        'titulo': 'Casos de prueba', 'id': 'identificador',
        'columnas': {
            'identificador': (True, 'texto'), 'nombre': (True, 'texto'), 'version': (True, 'texto'),
            'pasos': (True, 'texto'), 'resultado_esperado': (True, 'texto'), 'responsable': (True, 'texto'),
            'fecha_prevista': (True, 'fecha')}},
    'resultados': {
        'titulo': 'Resultados de prueba', 'id': None,
        'columnas': {
            'identificador_caso': (True, 'texto'), 'fecha_ejecucion': (True, 'fecha'),
            'resultado': (True, ('opciones', [r[0] for r in ResultadoPrueba.RESULTADOS])),
            'resultado_obtenido': (True, 'texto'), 'ejecutor': (True, 'texto'), 'evidencia': (True, 'texto')}},
    'defectos': {
        'titulo': 'Defectos', 'id': 'identificador',
        'columnas': {
            'identificador': (True, 'texto'), 'descripcion': (True, 'texto'),
            'severidad': (True, ('opciones', [s[0] for s in Defecto.SEVERIDADES])),
            'estado': (True, ('opciones', [e[0] for e in Defecto.ESTADOS])), 'fecha_reporte': (True, 'fechahora'),
            'responsable': (True, 'texto'), 'fecha_cierre': (False, 'fechahora'), 'verificado_por': (False, 'texto'),
            'evidencia': (True, 'texto')}},
}


def plantilla_csv(tipo):
    salida = io.StringIO()
    csv.writer(salida).writerow(TIPOS[tipo]['columnas'])
    return salida.getvalue().encode('utf-8-sig')


def _convertir(valor, tipo):
    if tipo == 'texto':
        return valor
    if tipo == 'fecha':
        return datetime.strptime(valor, '%Y-%m-%d').date()
    if tipo == 'fechahora':
        for formato in ('%Y-%m-%d %H:%M', '%Y-%m-%dT%H:%M', '%Y-%m-%d'):
            try:
                return timezone.make_aware(datetime.strptime(valor, formato))
            except ValueError:
                continue
        raise ValueError
    if valor not in tipo[1]:
        raise ValueError
    return valor


def _leer(contenido):
    try:
        texto = contenido.decode('utf-8-sig')
    except UnicodeDecodeError:
        return None, [{'fila': 1, 'campo': '(archivo)', 'mensaje': 'El archivo debe estar codificado en UTF-8.'}]
    primera = texto.splitlines()[0] if texto.strip() else ''
    delimitador = ';' if primera.count(';') > primera.count(',') else ','
    lector = csv.DictReader(io.StringIO(texto), delimiter=delimitador)
    return lector, []


def validar(proyecto, tipo, contenido):
    """Devuelve (filas_convertidas, errores). Con errores, `filas_convertidas` no debe guardarse."""
    cfg = TIPOS[tipo]
    lector, errores = _leer(contenido)
    if errores:
        return [], errores
    esperadas = list(cfg['columnas'])
    if lector.fieldnames is None:
        return [], [{'fila': 1, 'campo': '(archivo)', 'mensaje': 'El archivo está vacío.'}]
    columnas = [c.strip() for c in lector.fieldnames]
    faltan = [c for c in esperadas if c not in columnas]
    sobran = [c for c in columnas if c not in esperadas]
    if faltan or sobran:
        detalle = (f'Faltan columnas: {", ".join(faltan)}. ' if faltan else '') + \
                  (f'Columnas no reconocidas: {", ".join(sobran)}.' if sobran else '')
        return [], [{'fila': 1, 'campo': '(encabezado)', 'mensaje': detalle.strip() + ' Usa la plantilla del sistema.'}]

    filas, vistos = [], set()
    existentes = _existentes(proyecto, tipo)
    for n, crudo in enumerate(lector, start=2):
        if n - 1 > MAX_FILAS:
            errores.append({'fila': n, 'campo': '(archivo)', 'mensaje': f'Máximo {MAX_FILAS} filas por archivo.'})
            break
        fila, errores_fila = {}, []
        for nombre, (obligatoria, kind) in cfg['columnas'].items():
            valor = (crudo.get(nombre) or '').strip()
            if not valor:
                if obligatoria:
                    errores_fila.append((nombre, 'Campo obligatorio vacío.'))
                fila[nombre] = None
                continue
            try:
                fila[nombre] = _convertir(valor, kind)
            except ValueError:
                msg = {'fecha': 'Fecha inválida (use AAAA-MM-DD).',
                       'fechahora': 'Fecha/hora inválida (use AAAA-MM-DD o AAAA-MM-DD HH:MM).'}.get(
                    kind if isinstance(kind, str) else '', f'Valor no permitido. Opciones: {", ".join(kind[1])}.'
                    if not isinstance(kind, str) else 'Valor inválido.')
                errores_fila.append((nombre, msg))
        errores_fila += _reglas_cruzadas(tipo, fila, crudo, proyecto, existentes, vistos)
        errores += [{'fila': n, 'campo': c, 'mensaje': m} for c, m in errores_fila]
        filas.append(fila)
    if not filas and not errores:
        errores.append({'fila': 2, 'campo': '(archivo)', 'mensaje': 'El archivo no contiene registros.'})
    return filas, errores


def _existentes(proyecto, tipo):
    if tipo == 'actividades':
        return set(Actividad.objects.filter(proyecto=proyecto).values_list('codigo', flat=True))
    if tipo == 'casos':
        return set(CasoPrueba.objects.filter(proyecto=proyecto).values_list('codigo', flat=True))
    if tipo == 'defectos':
        return set(Defecto.objects.filter(proyecto=proyecto).values_list('codigo', flat=True))
    return {(r.caso.codigo, r.fecha_ejecucion, r.resultado)
            for r in ResultadoPrueba.objects.filter(caso__proyecto=proyecto).select_related('caso')}


def _reglas_cruzadas(tipo, fila, crudo, proyecto, existentes, vistos):
    errores = []
    if tipo == 'resultados':
        codigo = fila.get('identificador_caso')
        if codigo and not CasoPrueba.objects.filter(proyecto=proyecto, codigo=codigo).exists():
            errores.append(('identificador_caso', 'No existe un caso con ese identificador en este proyecto.'))
        llave = (codigo, fila.get('fecha_ejecucion'), fila.get('resultado'))
        if None not in llave and (llave in existentes or llave in vistos):
            errores.append(('identificador_caso', 'Resultado duplicado (mismo caso, fecha y resultado): importación repetida.'))
        vistos.add(llave)
        return errores
    codigo = fila.get('identificador')
    if codigo:
        if codigo in vistos:
            errores.append(('identificador', 'Identificador duplicado dentro del archivo.'))
        elif codigo in existentes:
            errores.append(('identificador', 'Identificador ya registrado en este proyecto (importación repetida).'))
        vistos.add(codigo)
    if tipo == 'defectos' and fila.get('estado') == 'Cerrado':
        if not fila.get('fecha_cierre'):
            errores.append(('fecha_cierre', 'Un defecto cerrado requiere fecha de cierre verificado.'))
        elif fila.get('fecha_reporte') and fila['fecha_cierre'] < fila['fecha_reporte']:
            errores.append(('fecha_cierre', 'El cierre no puede ser anterior al reporte.'))
        if not fila.get('verificado_por'):
            errores.append(('verificado_por', 'Indica quién verificó el cierre.'))
    return errores


@transaction.atomic
def guardar(proyecto, tipo, filas):
    """Guarda todas las filas ya validadas en una sola transacción."""
    if tipo == 'actividades':
        for f in filas:
            Actividad.objects.create(proyecto=proyecto, codigo=f['identificador'], nombre=f['nombre'], tipo=f['tipo'],
                                     responsable=f['responsable'], fecha_prevista=f['fecha_prevista'], estado=f['estado'],
                                     fecha_terminada=f['fecha_terminada'], evidencia=f['evidencia'])
    elif tipo == 'casos':
        for f in filas:
            CasoPrueba.objects.create(proyecto=proyecto, codigo=f['identificador'], nombre=f['nombre'],
                                      version=f['version'], pasos=f['pasos'], resultado_esperado=f['resultado_esperado'],
                                      responsable=f['responsable'], fecha_prevista=f['fecha_prevista'])
    elif tipo == 'resultados':
        for f in filas:
            caso = CasoPrueba.objects.get(proyecto=proyecto, codigo=f['identificador_caso'])
            ResultadoPrueba.objects.create(caso=caso, fecha_ejecucion=f['fecha_ejecucion'], resultado=f['resultado'],
                                           resultado_obtenido=f['resultado_obtenido'], ejecutor=f['ejecutor'],
                                           evidencia=f['evidencia'])
    else:
        for f in filas:
            Defecto.objects.create(proyecto=proyecto, codigo=f['identificador'], descripcion=f['descripcion'],
                                   severidad=f['severidad'], estado=f['estado'], fecha_reporte=f['fecha_reporte'],
                                   responsable=f['responsable'], fecha_cierre=f['fecha_cierre'],
                                   verificado_por=f['verificado_por'] or '', evidencia=f['evidencia'])
    return len(filas)
