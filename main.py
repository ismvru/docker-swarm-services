#!/usr/bin/env python3
from flask import Flask, Response
from os.path import exists
import docker
import logging
import json
import configparser
import time

# Основная конфигурация
config = configparser.ConfigParser()
config.read("config.ini")
if not exists("config.ini"):
    config["app"] = {
        "loglevel": "INFO",
        "delta": 600,
        "blacklist": "",
        "header": "docker_swarm"
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
                "docker_swarm": [
                    {
                        "short_id": "ijv2qdz7jl",
                        "name": "portainer-agent_agent",
                        "image": "agent",
                        "tag": "2.10.0"
                    },
                    {
                        "short_id": "p2d2qqf1pb",
                        "name": "nginx-proxy-manager-external_nginx",
                        "image": "nginx-proxy-manager",
                        "tag": "latest"
                    }
                ]
            }
        Сохраняет JSON в временный файл CachedResp.json рядом с main.py
        """
        logging.info("Docker api query started")
        # Единственный запрос к API Docker
        services = self.client.services.list()
        result = {config["app"]["header"]: []}
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
                # Добавляем временный словарь в массив в основном словаре
                result[config["app"]["header"]].append(tmpdct)
        logging.info("Docker api query finished")
        # Пишем ответ в виде JSON в файл
        with open("CachedResp.json", "w") as cache_file:
            cache_file.write(json.dumps(result, indent=2))
        return result


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
        if not exists("CachedResp.json"):
            list = json.dumps(lister.get_service_list())
        # Если прошло больше чем app.delta времени
        elif (int(time.time()) - lister.last_query_time > int(
                config["app"]["delta"])):
            list = json.dumps(lister.get_service_list())
        # Ну или отдаём из кеша
        else:
            with open("CachedResp.json", "r") as cache_file:
                list = cache_file.read()
        resp = Response(list)
        resp.headers["Content-Type"] = "application/json"
        return resp

    api.run(host=config["http"]["host"], port=config["http"]["port"])
