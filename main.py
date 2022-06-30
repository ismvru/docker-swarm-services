from fastapi import FastAPI, HTTPException, Response, Request
from fastapi.responses import ORJSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from os.path import exists
import logging
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
        "attachment_id": 123456789,
        "start_time": "",
        "end_time": "",
        "sleep_time": 600
    }
    with open('config.ini', 'w') as configfile:
        config.write(configfile)
logging.basicConfig(
    level=config["app"]["loglevel"],
    format=  # noqa: E251
    '%(asctime)s.%(msecs)03d %(levelname)s %(module)s - %(funcName)s: %(message)s',  # noqa: E501
    datefmt='%Y-%m-%d %H:%M:%S')


@dataclass
class mime:
    xml: str = "text/xml"
    yaml: str = "text/yaml"


header = config["app"]["header"]
without_tasks = config.getboolean("app", "without_tasks")
blacklist = config["app"]["blacklist"]
timezone = config["app"]["timezone"]
try:
    run_updater = config.getboolean("confluence", "run_updater")
except Exception:
    run_updater = False
if run_updater:
    try:
        if config["confluence"]["start_time"] == "":
            start_time = None
        else:
            start_time = config["app"]["start_time"]
        if config["confluence"]["end_time"] == "":
            end_time = None
        else:
            end_time = config["confluence"]["end_time"]
    except KeyError:
        start_time = None
        end_time = None
    try:
        sleep_time = config.getint("confluence", "sleep_time")
    except configparser.NoOptionError:
        sleep_time = 600

# Если у нас config["confluence"]["run_updater"] == True
# запускаем обновлятор в отдельном потоке
try:
    if run_updater:
        import threading
        updater = confluence.ConfluenceUploader()
        updater_thread = threading.Thread(target=updater.worker,
                                          name="ConfluenceUploader.worker",
                                          kwargs={
                                              "start_time": start_time,
                                              "end_time": end_time,
                                              "sleep_time": sleep_time
                                          })
        updater_thread.start()
except Exception:
    exit(1)

# Инициализируем класс
lister = serviceslister.ServicesLister()
logging.info("Start api")

app = FastAPI(redoc_url=None)
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


# Api responses
@app.get("/")
async def get_list(format: str | None = None):
    """Get services list"""
    if format not in ["xml", "json", "yaml", "yml", None]:
        raise HTTPException(
            400, detail=f'format must be json/xml/yaml/yml, not {format}')
    service_list = lister.get_service_list(header=header,
                                           without_tasks=without_tasks,
                                           blacklist=blacklist,
                                           timezone=timezone)
    if format in [None, "json"]:
        resp = ORJSONResponse(content=service_list)
    elif format == "xml":
        resp = Response(content=dict2xml(service_list), media_type=mime.xml)
    elif format in ["yml", "yaml"]:
        resp = Response(content=yaml.dump(service_list), media_type=mime.yaml)
    return resp


@app.get("/ajax")
async def get_list_for_ajax():
    """Get services list for datatable"""
    return ORJSONResponse(
        lister.get_service_list(header=header,
                                without_tasks=without_tasks,
                                blacklist=blacklist,
                                timezone=timezone,
                                ajax=True))


@app.get("/table", response_class=HTMLResponse)
async def render_table(request: Request):
    """Render datatable"""
    return templates.TemplateResponse("table.html", {"request": request})
