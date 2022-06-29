#!/bin/bash
set -x
mkdir -p logs

gunicorn --bind 0.0.0.0:8080 --reuse-port main:app
