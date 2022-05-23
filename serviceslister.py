#!/usr/bin/env python3
import docker
import logging
from typing import Any
import json
import arrow


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

    def get_service_list(self,
                         header: str = "docker_swarm",
                         without_tasks: bool = False,
                         blacklist: str = "",
                         cachefile: str = "CachedResp.json",
                         timezone: str = "GMT",
                         ajax=False) -> Any:
        """Получение списка служб и генерация ответа
        Сохраняет JSON в временный файл CachedResp.json рядом с main.py
        """
        logging.info("Docker api query started")
        # Единственный запрос к API Docker
        services = self.client.services.list()
        result = {"cluster_name": header, "data": []}
        for service in services:
            if len(service.tasks()) == 0 and not without_tasks:
                continue
            if service.name in blacklist.split(","):
                continue
            # Создаём временный словарь для хранения результата
            tmpdct = {}
            # Добавляем в него короткий ID сервиса
            tmpdct["short_id"] = service.short_id
            # Добавляем имя сервиса
            tmpdct["name"] = service.name
            # Добавляем имя стека
            tmpdct["stack"] = service.name.rsplit('_', 1)[0]
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
                service.attrs["CreatedAt"], timezone=timezone)[0]
            tmpdct["created_human"] = self.timestr_humanize(
                service.attrs["CreatedAt"], timezone=timezone)[1]
            tmpdct["updated"] = self.timestr_humanize(
                service.attrs["UpdatedAt"], timezone=timezone)[0]
            tmpdct["updated_human"] = self.timestr_humanize(
                service.attrs["UpdatedAt"], timezone=timezone)[1]
            # Режим репликации
            tmpdct["replication_mode"] = list(
                service.attrs["Spec"]["Mode"].keys())[0]
            if tmpdct["replication_mode"] == "Replicated":
                tmpdct["replica_count"] = service.attrs["Spec"]["Mode"][
                    "Replicated"]["Replicas"]
            else:
                tmpdct["replica_count"] = len(self.client.nodes.list())
            tasks_running = 0
            tasks_shutdown = 0
            for task in service.tasks():
                if task["DesiredState"] == "running":
                    tasks_running += 1
                elif task["DesiredState"] == "shutdown":
                    tasks_shutdown += 1
            tmpdct["tasks_count"] = len(service.tasks())
            tmpdct["tasks_running"] = tasks_running
            tmpdct["tasks_shutdown"] = tasks_shutdown
            tmpdct["cluster_name"] = header
            # Добавляем временный словарь в массив в основном словаре
            result["data"].append(tmpdct)
        logging.info("Docker api query finished")
        # Пишем ответ в виде JSON в файл
        with open(cachefile, "w") as cache_file:
            cache_file.write(json.dumps(result, indent=2))
        if ajax:
            return result
        else:
            return [result]

    def timestr_humanize(self, timestr: str, timezone="GMT") -> tuple:
        utcdate = arrow.get(timestr)
        localdate = utcdate.to(timezone)
        return (localdate.format(), localdate.humanize())