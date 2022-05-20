#!/usr/bin/env python3
from flask import Flask, Response, render_template
from os.path import exists
import docker
import logging
import json
import configparser
import time
import arrow
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
        "timezone": "Europe/Moscow"
    }
    loglevel = config["app"]["loglevel"]
    config["http"] = {"host": "0.0.0.0", "port": 8080}  # nosec
    with open('config.ini', 'w') as configfile:
        config.write(configfile)
logging.basicConfig(level=config["app"]["loglevel"])


class ServicesLister:
    """Основной класс приложения.
    Общение с докером происходит именно здесь"""

    def __init__(self) -> None:
        """Инициализируем все переменные"""
        try:
            self.client = docker.from_env()
        except Exception as e:
            # Если не смогли подключиться к Docker - выходим
            logging.exception(e)
            exit(1)
        try:
            self.swarm_version = self.client.swarm.version
        except AttributeError as e:
            # Если не swarm - тоже выходим
            logging.exception(e)
            exit(1)
        self.last_query_time = 0
        logging.debug(f"{self.swarm_version = }")

    def get_service_list(self) -> dict:
        """Получение списка служб и генерация ответа
        Возвращает словарь формата:
            {
            "cluster_name": "docker_swarm",
            "data": [
                {
                "short_id": "ijv2qdz7jl",
                "name": "portainer-agent_agent",
                "image": "agent",
                "tag": "2.10.0",
                "created": "2022-03-06 20:31:00+03:00",
                "created_human": "2 months ago",
                "updated": "2022-05-01 18:00:31+03:00",
                "updated_human": "2 weeks ago"
                },
                {
                "short_id": "p2d2qqf1pb",
                "name": "nginx-proxy-manager-external_nginx",
                "image": "nginx-proxy-manager",
                "tag": "latest",
                "created": "2022-05-01 18:13:17+03:00",
                "created_human": "2 weeks ago",
                "updated": "2022-05-01 18:13:17+03:00",
                "updated_human": "2 weeks ago"
                }
            ]
            }
        Сохраняет JSON в временный файл CachedResp.json рядом с main.py
        """
        logging.info("Docker api query started")
        # Единственный запрос к API Docker
        services = self.client.services.list()
        result = {
            "cluster_name": config["app"]["header"],
            "data": []
        }
        for service in services:
            if service.name not in config["app"]["blacklist"].split(","):
                # Создаём временный словарь для хранения результата
                tmpdct = {}
                # Добавляем в него короткий ID сервиса
                tmpdct["short_id"] = service.short_id
                # Добавляем имя сервиса
                tmpdct["name"] = service.name
                # Вытаскиваем все метки
                labels = service.attrs["Spec"]["Labels"]
                # Имя Docker образа без registry
                image = labels["com.docker.stack.image"].split("/")[-1]
                # Сам Docker образ без тега
                tmpdct["image"] = image.split(":")[0]
                # Тег Docker образа
                tmpdct["tag"] = image.split(":")[-1]
                # Created и Updated
                tmpdct["created"] = self.timestr_humanize(
                    service.attrs["CreatedAt"])[0]
                tmpdct["created_human"] = self.timestr_humanize(
                    service.attrs["CreatedAt"])[1]
                tmpdct["updated"] = self.timestr_humanize(
                    service.attrs["UpdatedAt"])[0]
                tmpdct["updated_human"] = self.timestr_humanize(
                    service.attrs["UpdatedAt"])[1]
                # Добавляем временный словарь в массив в основном словаре
                result["data"].append(tmpdct)
        logging.info("Docker api query finished")
        # Пишем ответ в виде JSON в файл
        with open(config["app"]["cachefile"], "w") as cache_file:
            cache_file.write(json.dumps(result, indent=2))
        return result

    def timestr_humanize(self, timestr: str) -> tuple:
        timezone = config["app"]["timezone"]
        utcdate = arrow.get(timestr)
        localdate = utcdate.to(timezone)
        return (localdate.format(), localdate.humanize())


if __name__ == "__main__":
    # Инициализируем класс
    lister = ServicesLister()
    logging.info("Start api")
    # Инициализируем приложение
    api = Flask(__name__)

    # Добавляем обработку запроса "GET /"
    @api.route('/', methods=['GET'])
    def get_list():
        # Если нет CachedResp.json
        if not exists(config["app"]["cachefile"]):
            service_list = json.dumps(lister.get_service_list())
        # Если прошло больше чем app.delta времени
        elif (int(time.time()) - lister.last_query_time > int(
                config["app"]["delta"])):
            service_list = json.dumps(lister.get_service_list())
        # Ну или отдаём из кеша
        else:
            with open(config["app"]["cachefile"], "r") as cache_file:
                service_list = cache_file.read()
        resp = Response(service_list)
        resp.headers["Content-Type"] = "application/json"
        return resp

    @api.route('/table', methods=['GET'])
    def render_table():
        return render_template("table.html")
    api.run(host=config["http"]["host"], port=config["http"]["port"])
