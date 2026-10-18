# PSPS Control SQA

Plataforma web de seguimiento de calidad de software (Django 5.2 + PostgreSQL).
Proyecto de Calidad de Software, UAZ Campus Siglo XXI.

Guía completa de instalación y uso: `docs/06_Guia_de_Instalacion_y_Uso.docx` (o su PDF en `docs/pdf/`).

## Arranque rápido

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Requiere PostgreSQL con una base `psps_sqa` (ver `docker-compose.yml`). Variables: `POSTGRES_DB`, `POSTGRES_USER`,
`POSTGRES_PASSWORD`, `POSTGRES_HOST`, `POSTGRES_PORT`.

## Pruebas

```bash
python manage.py test -v 2
```

## Datos de ejemplo (ficticios)

En `datos_prueba/` hay 4 CSV de ejemplo para importar (casos antes que resultados).


```bash
python manage.py cargar_demo
```
