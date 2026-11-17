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

## Despliegue (Render)

El producto está desplegado en: **https://psps-control-sqa.onrender.com**
Cómo se despliega (detalle en `docs/06_Guia_de_Instalacion_y_Uso.docx`, sección «Despliegue»):

1. En [render.com](https://render.com), **New → Blueprint**, elegir este repositorio. El archivo `render.yaml` crea el servicio web y la base PostgreSQL.
2. Render ejecuta `build.sh` (instala dependencias, reúne los estáticos y aplica las migraciones) y arranca con `gunicorn config.wsgi:application`.
3. Variables de entorno (las fija el blueprint): `DJANGO_DEBUG=0`, `DJANGO_SECRET_KEY` (generada), `DATABASE_URL` (de la base), `RENDER_EXTERNAL_HOSTNAME` (la pone Render).
4. Cada `git push` a `main` vuelve a desplegar.

Notas: en el plan gratuito el servicio se suspende tras 15 min sin uso y la primera carga tarda cerca de un minuto; la base gratuita caduca a los 30 días (hay que crearla de nuevo o pasar a un plan de pago). Para ejecutar las pruebas en el servidor: pestaña **Shell** del servicio → `python manage.py test`.
