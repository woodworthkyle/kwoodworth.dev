#!/bin/bash

source ~/.bashrc
micromamba activate django
python manage.py collectstatic
sudo systemctl restart gunicorn