#!/bin/bash
set -x
mkdir -p logs

case $1 in
"fastapi") uvicorn --host 0.0.0.0 --port 8080 --http httptools --loop uvloop main-fastapi:app ;;
"flask") gunicorn --bind 0.0.0.0:8080 --reuse-port main:app ;;
*) echo "Please provide argument. fastapi or flask?" ;;
esac
