#!/bin/bash

source ~/.bashrc
micromamba activate django
python manage.py collectstatic

# This starts a dev server technically
python manage.py runserver