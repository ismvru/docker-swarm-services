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
for section in config.sections():
    logging.debug(f"{dict(config.items(section)) = }")


@dataclass
class mime:
    xml: str = "text/xml"
    yaml: str = "text/yaml"


try:
    run_updater = config.getboolean("confluence", "run_updater")
except Exception:
    run_updater = False

# Если у нас config["confluence"]["run_updater"] == True
# запускаем обновлятор в отдельном потоке
try:
    if run_updater:
        logging.info("run_updater is True, starting updater")
        import threading
        updater = confluence.ConfluenceUploader()
        updater_thread = threading.Thread(target=updater.worker,
                                          name="ConfluenceUploader.worker")
        updater_thread.start()
except Exception as e:
    logging.exception(e)
    exit(1)

# Инициализируем класс
lister = serviceslister.ServicesLister()
logging.info("Init api")

app = FastAPI(redoc_url=None)
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


# Api responses
@app.get("/")
async def get_list(format: str | None = None):
    """Get services list"""
    logging.debug(f"/ - {format = }")
    if format not in ["xml", "json", "yaml", "yml", None]:
        raise HTTPException(
            400, detail=f'format must be json/xml/yaml/yml, not {format}')
    service_list = lister.get_service_list(
        header=config["app"]["header"],
        without_tasks=config.getboolean("app", "without_tasks"),
        blacklist=config["app"]["blacklist"],
        timezone=config["app"]["timezone"])
    if format in [None, "json"]:
        logging.debug("Render JSON")
        resp = ORJSONResponse(content=service_list)
    elif format == "xml":
        logging.debug("Render XML")
        resp = Response(content=dict2xml(service_list), media_type=mime.xml)
    elif format in ["yml", "yaml"]:
        logging.debug("Render YAML")
        resp = Response(content=yaml.dump(service_list), media_type=mime.yaml)
    return resp


@app.get("/ajax")
async def get_list_for_ajax(request: Request):
    """Get services list for datatable"""
    logging.debug(f"{request = }")
    return ORJSONResponse(
        lister.get_service_list(header=config["app"]["header"],
                                without_tasks=config.getboolean(
                                    "app", "without_tasks"),
                                blacklist=config["app"]["blacklist"],
                                timezone=config["app"]["timezone"],
                                ajax=True))


@app.get("/table", response_class=HTMLResponse)
async def render_table(request: Request):
    """Render datatable"""
    logging.debug(f"{request = }")
    return templates.TemplateResponse("table.html", {"request": request})
