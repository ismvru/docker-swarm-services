#!/usr/bin/env python3
import requests
import json
import logging
import arrow
from time import sleep


class ConfluenceUploader:

    def __init__(self,
                 confluence_url: str,
                 confluence_token: str,
                 page_id: int,
                 attachment_id: int | str,
                 delta: int = None) -> None:
        """ConfluenceUploader
        confluence_url - Confluence server url
        confluence_token - Confluence token
        page_id - Confluence page ID
        attachment_id - Confluence attachment ID
        delta - delta between worker wake-ups"""
        logging.info("Init ConfluenceUploader - start")
        self.confluence = confluence_url
        self.token = confluence_token
        self.page_id = page_id
        self.page_url = f"{self.confluence}/rest/api/content/{self.page_id}"  # noqa: E501
        self.attachment_id = attachment_id,
        self.delta = delta
        self.headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {self.token}",
            "X-Atlassian-Token": "no-check"
        }
        self.latest_data: dict = {}
        # Test confluence api
        response = requests.get(f"{self.confluence}/rest/api/user/current")
        current_user = json.loads(response.text)
        logging.info(f"Current user: {current_user}")
        logging.info("Init ConfluenceUploader - done")

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

    def worker(self, port: int):
        if self.delta is None:
            raise RuntimeError(
                "Timedelta is None. Please reinit class with delta arg")
        while True:
            logging.info(
                "Wake up, Neo. The Matrix has you. Getting swarm services list..."  # noqa: E501
            )
            response = requests.get(f"http://localhost:{port}/")
            response_dict = json.loads(response.text)
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
                    tempfile.write(response.text)
                self.update_file(attachment_id=self.attachment_id,
                                 file_path="UpdaterTempFile.json")
                self.latest_data = tmpdct
                logging.info("Update complete!")
            logging.info("Sleeping...")
            sleep(self.delta)
