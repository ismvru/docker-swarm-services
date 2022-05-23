#!/usr/bin/env python3
from flask import Flask, Response, render_template, request, abort
from os.path import exists
import logging
import json
import configparser
import time
from serviceslister import ServicesLister
from dict2xml import dict2xml
import yaml
import toml

# Основная конфигурация
config = configparser.ConfigParser()
config.read("config.ini")
if not exists("config.ini"):
    config["app"] = {
        "loglevel": "INFO",
        "delta": 600,
        "blacklist": "",
        "header": "docker_swarm",
        "cachefile": "CachedResp.json",
        "timezone": "Europe/Moscow",
        "without_tasks": "no"
    }
    loglevel = config["app"]["loglevel"]
    config["http"] = {"host": "0.0.0.0", "port": 8080}  # nosec
    with open('config.ini', 'w') as configfile:
        config.write(configfile)
logging.basicConfig(level=config["app"]["loglevel"])

if __name__ == "__main__":
    header = config["app"]["header"]
    without_tasks = config.getboolean("app", "without_tasks")
    blacklist = config["app"]["blacklist"]
    cachefile = config["app"]["cachefile"]
    timezone = config["app"]["timezone"]

    # Инициализируем класс
    lister = ServicesLister()
    logging.info("Start api")
    # Инициализируем приложение
    api = Flask(__name__)

    # Добавляем обработку запроса "GET /"
    @api.route('/', methods=['GET'])
    def get_list():
        # Если нет CachedResp.json
        response_type = request.args.get('format')
        if response_type not in ["xml", "json", "yaml", "yml", "toml", None]:
            abort(
                400,
                f'format must be json/xml/yaml/yml/toml, not {response_type}')
        if not exists(cachefile):
            service_list = lister.get_service_list(header=header,
                                                   without_tasks=without_tasks,
                                                   blacklist=blacklist,
                                                   cachefile=cachefile,
                                                   timezone=timezone)
            if response_type in [None, "json"]:
                resp = Response(json.dumps(service_list))
                resp.headers["Content-Type"] = "application/json"
            elif response_type == "xml":
                resp = Response(dict2xml(service_list))
                resp.headers["Content-Type"] = "application/xml"
            elif response_type in ["yml", "yaml"]:
                resp = Response(yaml.dump(service_list))
                resp.headers["Content-Type"] = "application/yaml"
            elif response_type == "toml":
                resp = Response(toml.dumps(service_list))
                resp.headers["Content-Type"] = "application/toml"
        # Если прошло больше чем app.delta времени
        elif (int(time.time()) - lister.last_query_time > int(
                config["app"]["delta"])):
            service_list = lister.get_service_list(header=header,
                                                   without_tasks=without_tasks,
                                                   blacklist=blacklist,
                                                   cachefile=cachefile,
                                                   timezone=timezone)
            if response_type in [None, "json"]:
                resp = Response(json.dumps(service_list))
                resp.headers["Content-Type"] = "application/json"
            elif response_type == "xml":
                resp = Response(dict2xml(service_list))
                resp.headers["Content-Type"] = "application/xml"
            elif response_type in ["yml", "yaml"]:
                resp = Response(yaml.dump(service_list))
                resp.headers["Content-Type"] = "application/yaml"
            elif response_type == "toml":
                resp = Response(toml.dumps(service_list))
                resp.headers["Content-Type"] = "application/toml"
        # Ну или отдаём из кеша
        else:
            with open(cachefile, "r") as cache_file:
                service_list = json.loads(cache_file.read())
            if response_type in [None, "json"]:
                resp = Response(json.dumps(service_list))
                resp.headers["Content-Type"] = "application/json"
            elif response_type == "xml":
                resp = Response(dict2xml(service_list))
                resp.headers["Content-Type"] = "application/xml"
            elif response_type in ["yml", "yaml"]:
                resp = Response(yaml.dump(service_list))
                resp.headers["Content-Type"] = "application/yaml"
            elif response_type == "toml":
                resp = Response(toml.dumps(service_list))
                resp.headers["Content-Type"] = "application/toml"
        # resp = Response(service_list)
        # resp.headers["Content-Type"] = "application/json"
        return resp

    @api.route('/ajax', methods=['GET'])
    def get_list_for_ajax():
        # Если нет CachedResp.json
        if not exists(cachefile):
            service_list = json.dumps(
                lister.get_service_list(header=header,
                                        without_tasks=without_tasks,
                                        blacklist=blacklist,
                                        cachefile=cachefile,
                                        timezone=timezone,
                                        ajax=True))
        # Если прошло больше чем app.delta времени
        elif (int(time.time()) - lister.last_query_time > int(
                config["app"]["delta"])):
            service_list = json.dumps(
                lister.get_service_list(header=header,
                                        without_tasks=without_tasks,
                                        blacklist=blacklist,
                                        cachefile=cachefile,
                                        timezone=timezone,
                                        ajax=True))
        # Ну или отдаём из кеша
        else:
            with open(cachefile, "r") as cache_file:
                service_list = cache_file.read()
        resp = Response(service_list)
        resp.headers["Content-Type"] = "application/json"
        return resp

    @api.route('/table', methods=['GET'])
    def render_table():
        return render_template("table.html")

    api.run(host=config["http"]["host"], port=config["http"]["port"])
