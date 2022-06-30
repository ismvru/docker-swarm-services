#!/usr/bin/env python3
import requests
import json
import logging
import arrow
from time import sleep
import configparser
from .serviceslister import ServicesLister


class ConfluenceUploader:

    def __init__(self) -> None:
        """ConfluenceUploader"""
        logging.info("Init ConfluenceUploader - start")
        self.config = configparser.ConfigParser()
        self.config.read("config.ini")
        logging.info("Configuration file loaded")
        logging.info(f"Confluence address: {self.config['confluence']['url']}")
        self.page_url = f"{self.config['confluence']['url']}/rest/api/content/{self.config['confluence']['page_id']}"  # noqa: E501
        try:
            if self.config["confluence"]["start_time"] == "":
                self.start_time = None
            else:
                self.start_time = self.config["confluence"]["start_time"]
            if self.config["confluence"]["end_time"] == "":
                self.end_time = None
            else:
                self.end_time = self.config["confluence"]["end_time"]
        except Exception as e:
            logging.exception(e)
            logging.info("Will use default values for start_time and end_time")
            self.start_time = None
            self.end_time = None
        try:
            self.sleep_time = self.config.getint("confluence", "sleep_time")
        except Exception as e:
            logging.exception(e)
            logging.info("Will use default values for sleep_time")
            self.sleep_time = 600

        self.headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {self.config['confluence']['token']}",
            "X-Atlassian-Token": "no-check"
        }
        self.latest_data: dict = {}
        # Test confluence api
        response = requests.get(
            f"{self.config['confluence']['url']}/rest/api/user/current",
            headers=self.headers)
        current_user = json.loads(response.text)["username"]
        logging.info(f"{current_user = }")
        logging.info("Init ConfluenceUploader - done")
        logging.debug(f"{self.__dict__ = }")

    def update_file(self, attachment_id: str | int, file_path: str) -> bool:
        """Update attachment file
        attachment_id - int or str attachment ID
        file_path - path to fule, which rewrite attachment"""
        url = f"{self.page_url}/child/attachment/{attachment_id}/data"
        files = {file_path: open(file_path, 'rb')}
        formdata = {
            "file": files[file_path].read(),
            "comment":
            f"API: Update file with py-docker-swarm-versions.ConfluenceUploader at {self.timestr(timezone='Europe/Moscow')}",  # noqa: E501
            "minorEdit": "true"
        }
        response = requests.post(url,
                                 headers=self.headers,
                                 files=files,
                                 data=formdata)
        logging.debug(f"{response.text = }")
        if response.status_code == 200:
            return False
        return True

    def timestr(self, timezone="GMT") -> tuple:
        utcdate = arrow.now()
        localdate = utcdate.to(timezone)
        return localdate.format()

    def worker(self):
        """Background worker
        infinite trys to detect changes in docker services
        and push json to confluence if services is changed
        start_time: see is_worktime
        end_time: see is_worktime
        sleep_time: time for sleep between trys"""
        lister = ServicesLister()
        while True:
            logging.info("Wake up, Neo. The Matrix has you.")
            is_worktime = True
            if self.start_time is not None and self.end_time is not None:
                try:
                    is_worktime = self.is_worktime(self.start_time,
                                                   self.end_time)
                except arrow.parser.ParserMatchError as e:
                    logging.exception(e)
            logging.debug(f"{is_worktime = }")
            if is_worktime:
                logging.info("Getting swarm services list...")
                response_dict = lister.get_service_list(
                    header=self.config["app"]["header"],
                    without_tasks=self.config.getboolean(
                        "app", "without_tasks"),
                    blacklist=self.config["app"]["blacklist"],
                    timezone=self.config["app"]["timezone"])
                logging.info("Searching for changes")
                tmpdct = {}
                for service in response_dict[0]["data"]:
                    tmpdct[service["short_id"]] = {
                        "image": service["image"],
                        "tag": service["tag"],
                        "replica_running": service["replica_running"]
                    }
                if self.latest_data != tmpdct:
                    logging.info("Found changes in services. Updating...")
                    with open("UpdaterTempFile.json", "w") as tempfile:
                        tempfile.write(json.dumps(response_dict, indent=2))
                    self.update_file(attachment_id=self.config["confluence"]
                                     ["attachment_id"],
                                     file_path="UpdaterTempFile.json")
                    self.latest_data = tmpdct
                    logging.info("Update complete!")
                else:
                    logging.info("There is no changes.")
                logging.info("Going to sleep")
            else:
                logging.info(
                    f"Nope, i'll work in interval {self.start_time} - {self.end_time}"  # noqa: E501
                )
            sleep(self.sleep_time)

    def is_worktime(self, start_time: str, end_time: str) -> bool:
        """Decides if start_time <= now() <= end_time
        start_time: str - HH:mm (09:00, 15:51, etc...)
        end_time: str - HH:mm (09:00, 15:51, etc...)"""
        now_arw = arrow.now(self.config["app"]["timezone"])
        logging.debug(f"{now_arw = }")
        start_time = arrow.get(start_time, "HH:mm")
        start_time = now_arw.replace(hour=start_time.hour,
                                     minute=start_time.minute).floor("minute")
        logging.debug(f"{start_time = }")
        end_time = arrow.get(end_time, "HH:mm")
        end_time = now_arw.replace(hour=end_time.hour,
                                   minute=end_time.minute).floor("minute")
        logging.debug(f"{end_time = }")
        if start_time <= now_arw <= end_time:
            return True
        else:
            return False
