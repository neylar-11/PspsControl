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



## Bitácora de SQA

La bitácora viva del equipo está en Google Sheets:
https://docs.google.com/spreadsheets/d/1l4mDJDqk2-E_HDppz1oI5_ATxX0b2vGE5zbmhxZ29I0/edit

Antes de cada entrega (20 oct, 3 nov, 19 nov) el responsable de calidad guarda una copia
en `Bitacora_SQA.xlsx` en este repositorio. Las capturas y logs que la bitácora referencia
están en `evidencias/`.
