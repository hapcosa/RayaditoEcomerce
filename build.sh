#!/bin/bash
npm i 
npm run build
# Exit on error
set -o errexit
pip install -r requirements.txt
python3 manage.py makemigrations
python3 manage.py migrate
python3 manage.py collectstatic --no-imput
python3 manage.py runserver