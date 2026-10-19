## Requisito / defecto
<!-- RF-xx o DEF-xxx; si no hay, explica por qué -->

## Qué cambia y por qué


## Validaciones y riesgos que incluye


## Pruebas ejecutadas
<!-- comando y resultado, p. ej. `python manage.py test` → 77/77 OK -->

## Evidencia
<!-- captura, log o enlace -->

## Revisor asignado
<!-- @usuario; el autor no aprueba su propio cambio -->

---
### Lista de revisión (doc 04) — la llena el revisor
1. ¿Responde a un RF o defecto registrado?
2. ¿Incluye las validaciones necesarias (campos, fechas, valores, evidencia)?
3. ¿Respeta las capas? (vistas sin cálculo ni SQL; dominio sin HTML)
4. ¿Los indicadores solo se calculan en `metricas/servicio.py`?
5. ¿Hay pruebas nuevas o actualizadas, y pasan todas?
6. ¿Se conserva el funcionamiento de las partes relacionadas?
7. ¿Los hallazgos bloqueantes están atendidos?
8. ¿La revisión y su aprobación quedan registradas aquí?