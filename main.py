#!/usr/bin/env python3
from flask import Flask, Response, render_template, request, abort
from os.path import exists
import logging
import json
import configparser
import time
import serviceslister.serviceslister
from dict2xml import dict2xml
import yaml
from dataclasses import dataclass

# Основная конфигурация
config = configparser.ConfigParser()
config.read("config.ini")
if not exists("config.ini"):
    config["app"] = {
        "loglevel": "INFO",
        "delta": 600,
        "blacklist": "",
        "header": "docker_swarm",
        "timezone": "Europe/Moscow",
        "without_tasks": "no"
    }
    loglevel = config["app"]["loglevel"]
    config["http"] = {"host": "0.0.0.0", "port": 8080}  # nosec
    with open('config.ini', 'w') as configfile:
        config.write(configfile)
logging.basicConfig(level=config["app"]["loglevel"])


@dataclass
class mime:
    json: str = "application/json"
    xml: str = "text/xml"
    yaml: str = "text/yaml"


if __name__ == "__main__":
    header = config["app"]["header"]
    without_tasks = config.getboolean("app", "without_tasks")
    blacklist = config["app"]["blacklist"]
    timezone = config["app"]["timezone"]

    # Инициализируем класс
    lister = serviceslister.serviceslister.ServicesLister()
    logging.info("Start api")
    # Инициализируем приложение
    api = Flask(__name__)

    # Добавляем обработку запроса "GET /"
    @api.route('/', methods=['GET'])
    def get_list():
        # Если нет CachedResp.json
        response_type = request.args.get('format')
        if response_type not in ["xml", "json", "yaml", "yml", None]:
            abort(400,
                  f'format must be json/xml/yaml/yml, not {response_type}')
        if lister.last_response is None:
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

        # Если прошло больше чем app.delta времени
        elif (int(time.time()) - lister.last_query_time > int(
                config["app"]["delta"])):
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

        # Ну или отдаём из кеша
        else:
            service_list = lister.last_response
            if response_type in [None, "json"]:
                resp = Response(json.dumps(service_list), mimetype=mime.json)
            elif response_type == "xml":
                resp = Response(dict2xml(service_list), mimetype=mime.xml)
            elif response_type in ["yml", "yaml"]:
                resp = Response(yaml.dump(service_list), mimetype=mime.yaml)
        return resp

    @api.route('/ajax', methods=['GET'])
    def get_list_for_ajax():
        # Если нет CachedResp.json
        if lister.last_response_ajax is None:
            service_list = json.dumps(
                lister.get_service_list(header=header,
                                        without_tasks=without_tasks,
                                        blacklist=blacklist,
                                        timezone=timezone,
                                        ajax=True))
        # Если прошло больше чем app.delta времени
        elif (int(time.time()) - lister.last_query_time > int(
                config["app"]["delta"])):
            service_list = json.dumps(
                lister.get_service_list(header=header,
                                        without_tasks=without_tasks,
                                        blacklist=blacklist,
                                        timezone=timezone,
                                        ajax=True))
        # Ну или отдаём из кеша
        else:
            service_list = json.dumps(lister.last_response_ajax)
        resp = Response(service_list, mimetype=mime.json)
        return resp

    @api.route('/table', methods=['GET'])
    def render_table():
        return render_template("table.html")

    api.run(host=config["http"]["host"], port=config["http"]["port"])
