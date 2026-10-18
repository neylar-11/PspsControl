"""Servicio de métricas (capa de dominio).

Único lugar donde se calculan los cinco indicadores, sus semáforos y el estado general.
Lo usan el dashboard y el reporte, por lo que siempre muestran los mismos valores al mismo corte.
No depende de HTML ni de las vistas.
"""
from datetime import datetime, time

from django.db import transaction
from django.utils import timezone

VERDE, AMARILLO, ROJO, GRIS, NO_APLICA = 'verde', 'amarillo', 'rojo', 'gris', 'no_aplica'

# Política inicial del equipo (ajustable con justificación; no proviene de una norma ni del cliente)
UMBRALES_PORCENTAJE = {
    'pruebas_aprobadas': (95, 80),
    'avance_ejecucion': (90, 70),
    'cumplimiento_sqa': (90, 70),
}
NOMBRES = {
    'pruebas_aprobadas': 'Pruebas aprobadas',
    'avance_ejecucion': 'Avance de ejecución de pruebas',
    'defectos_criticos': 'Defectos críticos abiertos',
    'cumplimiento_sqa': 'Cumplimiento de actividades SQA',
    'tiempo_resolucion': 'Tiempo promedio de resolución',
}
ORDEN = list(NOMBRES)


def semaforo_porcentaje(valor, verde, amarillo):
    """>= verde → verde; >= amarillo → amarillo; menor → rojo (límites exactos incluidos)."""
    if valor >= verde:
        return VERDE
    if valor >= amarillo:
        return AMARILLO
    return ROJO


def semaforo_tiempo(promedio_horas, t):
    """<= T → verde; > T y <= 2T → amarillo; > 2T → rojo."""
    if promedio_horas <= t:
        return VERDE
    if promedio_horas <= 2 * t:
        return AMARILLO
    return ROJO


def estado_general(indicadores):
    """Rojo si algún indicador está en rojo; gris si falta información; amarillo; verde.

    Los no aplicables se excluyen (su motivo queda visible en cada indicador).
    """
    estados = [i['estado'] for i in indicadores if i['estado'] != NO_APLICA]
    if not estados:
        return GRIS, 'Ningún indicador es aplicable al corte.'
    if ROJO in estados:
        return ROJO, 'Al menos un indicador está en rojo.'
    if GRIS in estados:
        return GRIS, 'Falta información para evaluar un indicador aplicable.'
    if AMARILLO in estados:
        return AMARILLO, 'Al menos un indicador está en amarillo.'
    return VERDE, 'Todos los indicadores aplicables están en verde.'


def _indicador(clave, estado, valor=None, motivo='', num=None, den=None, regla='', unidad='%'):
    return {'clave': clave, 'nombre': NOMBRES[clave], 'estado': estado, 'valor': valor, 'motivo': motivo,
            'numerador': num, 'denominador': den, 'regla': regla, 'unidad': unidad, 'orden': ORDEN.index(clave)}


def _porcentaje(clave, num, den, motivo_sin_datos):
    if den == 0:
        return None
    verde, amarillo = UMBRALES_PORCENTAJE[clave]
    valor = round(num / den * 100, 1)
    return _indicador(clave, semaforo_porcentaje(valor, verde, amarillo), valor, '', num, den,
                      f'Verde ≥ {verde}% · Amarillo ≥ {amarillo}% y < {verde}% · Rojo < {amarillo}%')


def _regla_pct(clave):
    verde, amarillo = UMBRALES_PORCENTAJE[clave]
    return f'Verde ≥ {verde}% · Amarillo ≥ {amarillo}% y < {verde}% · Rojo < {amarillo}%'


def calcular(proyecto, corte):
    """Calcula los cinco indicadores de `proyecto` considerando solo registros hasta `corte` (inclusive)."""
    fin = timezone.make_aware(datetime.combine(corte, time.max))
    t = proyecto.objetivo_resolucion_horas
    indicadores, pendientes, evidencias = [], {'actividades': [], 'pruebas': [], 'defectos': []}, \
        {'actividades': [], 'resultados': [], 'defectos': []}

    # ── Pruebas ─────────────────────────────────────────────────────────────
    casos = list(proyecto.casos.prefetch_related('resultados'))
    ultimos = {c.pk: c.ultimo_resultado(corte) for c in casos}
    ejecutados = [c for c in casos if ultimos[c.pk]]
    aprobados = [c for c in ejecutados if ultimos[c.pk].resultado == 'Aprobada']
    previstos = [c for c in casos if c.fecha_prevista <= corte]
    previstos_ejecutados = [c for c in previstos if ultimos[c.pk]]
    for c in previstos:
        if not ultimos[c.pk]:
            pendientes['pruebas'].append({'codigo': c.codigo, 'nombre': c.nombre, 'fecha_prevista': str(c.fecha_prevista)})
    for c in ejecutados:
        r = ultimos[c.pk]
        evidencias['resultados'].append({'codigo': c.codigo, 'fecha': str(r.fecha_ejecucion), 'resultado': r.resultado,
                                         'evidencia': r.evidencia})

    if not ejecutados:
        indicadores.append(_indicador('pruebas_aprobadas', GRIS, None, 'Sin pruebas ejecutadas al corte.', 0, 0,
                                      _regla_pct('pruebas_aprobadas')))
    else:
        indicadores.append(_porcentaje('pruebas_aprobadas', len(aprobados), len(ejecutados), ''))

    if not casos:
        indicadores.append(_indicador('avance_ejecucion', GRIS, None, 'No hay casos de prueba registrados.', 0, 0,
                                      _regla_pct('avance_ejecucion')))
    elif not previstos:
        indicadores.append(_indicador('avance_ejecucion', NO_APLICA, None, 'No hay pruebas previstas al corte.', 0, 0,
                                      _regla_pct('avance_ejecucion')))
    else:
        indicadores.append(_porcentaje('avance_ejecucion', len(previstos_ejecutados), len(previstos), ''))

    # ── Defectos ────────────────────────────────────────────────────────────
    defectos = [d for d in proyecto.defectos.all() if d.fecha_reporte <= fin]

    def cerrado_al_corte(d):
        return d.estado == 'Cerrado' and d.fecha_cierre is not None and d.fecha_cierre <= fin

    abiertos = [d for d in defectos if not cerrado_al_corte(d)]
    criticos = [d for d in abiertos if d.severidad == 'Crítica']
    for d in abiertos:
        pendientes['defectos'].append({'codigo': d.codigo, 'severidad': d.severidad, 'descripcion': d.descripcion[:120]})
    for d in defectos:
        evidencias['defectos'].append({'codigo': d.codigo, 'evidencia': d.evidencia})

    regla_crit = 'Verde = 0 · Amarillo no aplica · Rojo ≥ 1'
    if not defectos and not proyecto.registro_defectos_confirmado:
        indicadores.append(_indicador('defectos_criticos', GRIS, None,
                                      'Sin defectos registrados y sin confirmar el registro: no se asume cero.', None, None,
                                      regla_crit, 'casos'))
    else:
        indicadores.append(_indicador('defectos_criticos', ROJO if criticos else VERDE, float(len(criticos)), '', None, None,
                                      regla_crit, 'casos'))

    cerrados = [d for d in defectos if cerrado_al_corte(d)]
    regla_t = f'T = {t} h · Verde ≤ {t} h · Amarillo ≤ {2 * t} h · Rojo > {2 * t} h'
    if cerrados:
        horas = [(d.fecha_cierre - d.fecha_reporte).total_seconds() / 3600 for d in cerrados]
        promedio = round(sum(horas) / len(horas), 1)
        indicadores.append(_indicador('tiempo_resolucion', semaforo_tiempo(promedio, t), promedio, '', sum(horas),
                                      len(cerrados), regla_t, 'h'))
    elif not defectos and proyecto.registro_defectos_confirmado:
        indicadores.append(_indicador('tiempo_resolucion', NO_APLICA, None, 'No hay defectos reportados al corte.', None,
                                      0, regla_t, 'h'))
    else:
        indicadores.append(_indicador('tiempo_resolucion', GRIS, None,
                                      'Aún no hay defectos con cierre verificado al corte.', None, 0, regla_t, 'h'))

    # ── Actividades SQA ─────────────────────────────────────────────────────
    actividades = list(proyecto.actividades.all())
    exigibles = [a for a in actividades if a.fecha_prevista <= corte]
    terminadas = [a for a in exigibles if a.estado == 'Terminada' and a.fecha_terminada and a.fecha_terminada <= corte
                  and a.evidencia.strip()]
    for a in exigibles:
        if a not in terminadas:
            pendientes['actividades'].append({'codigo': a.codigo, 'nombre': a.nombre, 'estado': a.estado,
                                              'fecha_prevista': str(a.fecha_prevista)})
    for a in terminadas:
        evidencias['actividades'].append({'codigo': a.codigo, 'evidencia': a.evidencia})
    if not actividades:
        indicadores.append(_indicador('cumplimiento_sqa', GRIS, None, 'No hay actividades SQA registradas.', 0, 0,
                                      _regla_pct('cumplimiento_sqa')))
    elif not exigibles:
        indicadores.append(_indicador('cumplimiento_sqa', NO_APLICA, None, 'No hay actividades exigibles al corte.', 0, 0,
                                      _regla_pct('cumplimiento_sqa')))
    else:
        indicadores.append(_porcentaje('cumplimiento_sqa', len(terminadas), len(exigibles), ''))

    indicadores.sort(key=lambda i: i['orden'])
    general, motivo = estado_general(indicadores)
    return {'indicadores': indicadores, 'estado_general': general, 'motivo_general': motivo,
            'umbrales': {'porcentajes': {k: {'verde': v[0], 'amarillo': v[1]} for k, v in UMBRALES_PORCENTAJE.items()},
                         'defectos_criticos': {'verde': 0, 'rojo': 1}, 'tiempo_resolucion_T_horas': t},
            'detalle': {'pendientes': pendientes, 'evidencias': evidencias}}


@transaction.atomic
def registrar_corte(proyecto, fecha=None):
    """Calcula y guarda el corte de `fecha` (hoy por omisión).

    Solo reemplaza el corte de esa misma fecha; las mediciones de otros cortes no se tocan.
    """
    from .models import Corte, Medicion
    fecha = fecha or timezone.localdate()
    r = calcular(proyecto, fecha)
    corte, _ = Corte.objects.update_or_create(
        proyecto=proyecto, fecha_corte=fecha,
        defaults={'estado_general': r['estado_general'], 'motivo_general': r['motivo_general'],
                  'umbrales': r['umbrales'], 'detalle': r['detalle']})
    corte.mediciones.all().delete()
    Medicion.objects.bulk_create([
        Medicion(corte=corte, clave=i['clave'], nombre=i['nombre'], valor=i['valor'], unidad=i['unidad'],
                 estado=i['estado'], motivo=i['motivo'], numerador=i['numerador'], denominador=i['denominador'],
                 regla=i['regla'], orden=i['orden']) for i in r['indicadores']])
    return corte


def ultimo_corte(proyecto):
    return proyecto.cortes.order_by('-fecha_corte').first()


def corte_solicitado(proyecto, texto_fecha):
    """Devuelve el corte pedido por fecha (AAAA-MM-DD) o, si no hay, el más reciente."""
    if texto_fecha:
        try:
            fecha = datetime.strptime(texto_fecha, '%Y-%m-%d').date()
        except ValueError:
            return ultimo_corte(proyecto)
        return proyecto.cortes.filter(fecha_corte=fecha).first() or ultimo_corte(proyecto)
    return ultimo_corte(proyecto)
