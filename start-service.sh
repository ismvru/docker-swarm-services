#!/bin/bash
set -x
uvicorn --host 0.0.0.0 --port 8080 --http httptools --loop uvloop main:app