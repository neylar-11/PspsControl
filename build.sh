#!/usr/bin/env bash
# Comando de construcción para Render (ver docs/06 y README, sección Despliegue)
set -o errexit
pip install -r requirements.txt
python manage.py collectstatic --noinput
python manage.py migrate
