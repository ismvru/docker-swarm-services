#!/usr/bin/env python3
from flask import Flask, Response, render_template, request, abort
from os.path import exists
import logging
import json
import configparser
from helpers import serviceslister
from helpers import confluence
from dict2xml import dict2xml
import yaml
from dataclasses import dataclass

# Основная конфигурация
config = configparser.ConfigParser()
config.read("config.ini")
if not exists("config.ini"):
    config["app"] = {
        "loglevel": "INFO",
        "blacklist": "",
        "header": "docker_swarm",
        "timezone": "Europe/Moscow",
        "without_tasks": "no"
    }
    loglevel = config["app"]["loglevel"]
    config["confluence"] = {
        "run_updater": "no",
        "url": "https://confluence.example.com",
        "token": "YourTokenHere",
        "page_id": 123456789,
        "attachment_id": 123456789
    }
    with open('config.ini', 'w') as configfile:
        config.write(configfile)
logging.basicConfig(level=config["app"]["loglevel"])


@dataclass
class mime:
    json: str = "application/json"
    xml: str = "text/xml"
    yaml: str = "text/yaml"


header = config["app"]["header"]
without_tasks = config.getboolean("app", "without_tasks")
blacklist = config["app"]["blacklist"]
timezone = config["app"]["timezone"]
run_updater = config.getboolean("confluence", "run_updater")
# Если у нас config["confluence"]["run_updater"] == True
# запускаем обновлятор в отдельном потоке
try:
    if run_updater:
        import threading
        updater = confluence.ConfluenceUploader()
        updater_thread = threading.Thread(target=updater.worker,
                                          name="ConfluenceUploader.worker")
        updater_thread.start()
except Exception:
    exit(1)

# Инициализируем класс
lister = serviceslister.ServicesLister()
logging.info("Start api")
# Инициализируем приложение
api = Flask(__name__)


# Добавляем обработку запроса "GET /"
@api.route('/', methods=['GET'])
def get_list():
    response_type = request.args.get('format')
    if response_type not in ["xml", "json", "yaml", "yml", None]:
        abort(400, f'format must be json/xml/yaml/yml, not {response_type}')
    service_list = lister.get_service_list(header=header,
                                           without_tasks=without_tasks,
                                           blacklist=blacklist,
                                           timezone=timezone)
    if response_type in [None, "json"]:
        resp = Response(json.dumps(service_list), mimetype=mime.json)
    elif response_type == "xml":
        resp = Response(dict2xml(service_list), mimetype=mime.xml)
    elif response_type in ["yml", "yaml"]:
        resp = Response(yaml.dump(service_list), mimetype=mime.yaml)
    return resp


@api.route('/ajax', methods=['GET'])
def get_list_for_ajax():
    service_list = json.dumps(
        lister.get_service_list(header=header,
                                without_tasks=without_tasks,
                                blacklist=blacklist,
                                timezone=timezone,
                                ajax=True))
    resp = Response(service_list, mimetype=mime.json)
    return resp


@api.route('/table', methods=['GET'])
def render_table():
    return render_template("table.html")


api.run()
