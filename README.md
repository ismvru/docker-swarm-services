# Генератор списка запущенных сервисов в Docker stack в JSON
<!-- markdownlint-disable MD013 -->

- [Генератор списка запущенных сервисов в Docker stack в JSON](#генератор-списка-запущенных-сервисов-в-docker-stack-в-json)
  - [Требования](#требования)
  - [Конфигурация](#конфигурация)
  - [Сборка Docker образа](#сборка-docker-образа)
  - [Запуск](#запуск)
    - [venv](#venv)
    - [docker](#docker)
    - [docker-compose](#docker-compose)
  
Служба, которая подключается к `/var/run/docker.sock`, и отдаёт список запущенных сервисов в формате JSON

Пример ответа:

```json
{
  "cluster_name": "docker_swarm",
  "docker_swarm": [
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
```

Где:

- `short_id` - ID службы
- `name` - имя службы
- `image` - имя docker образа
- `tag` - тег docker образа
- `created` - Время создания сервиса
- `created_human` - Время создания сервиса в виде строки "столько времени назад"
- `updated` - Время обновления сервиса
- `updated_human` - Время обновления сервиса в виде строки "столько времени назад"

## Требования

- Python 3.8+
- python-flask
- python-docker
- python-arrow
- Кластер docker swarm
- Доступ на чтение к /var/run/docker.sock

## Конфигурация

При первом запуске создаёт файл `config.ini` со следующим содержимым:

```ini
[app]
loglevel = INFO
delta = 600
blacklist = 
header = docker_swarm
cachefile = CachedResp.json
timezone = Europe/Moscow

[http]
host = 0.0.0.0
port = 8080
```

Где:

- `app.loglevel` - уровень логирования службы. `DEBUG`/`INFO`/`WARNING`/`ERROR`
- `app.delta` - минимальное время между запросами к `/var/run/docker.sock` в секундах
- `app.blacklist` - список названий сервисов, разделённых запятой, которые не надо включать в JSON. `service_app1,service_app2,service_app3`
- `app.header` - имя корневого элемента JSON, а так же `cluster_name`. `"app.header": [`
- `app.cachefile` - путь до файла с кешем ответов от docker
- `app.timezone` - Временная зона для вывода created и updated. См. [список временных зон](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones), List -> TZ database name
- `http.host` - IP, на котором слушает HTTP служба. Один из IP хоста или `0.0.0.0`
- `http.port` - Порт, на котором слушает HTTP служба. Для использования портов <1024 нужны права пользователя `root` или привелегия `CAP_NET_ADMIN`

## Сборка Docker образа

```bash
docker build . --tag registry/image:tag
```

## Запуск

### venv

```bash
python -m venv .venv
source .venv/bin/activate
pip instarr -r req.txt
./main.py
```

### docker

Запуск со стандартной конфигурацией

```bash
docker run -d -p 8080:8080 -v /var/run/docker.sock:/var/run/docker.sock:ro registry/image:tag
```

Запуск со своей конфигурацией

```bash
docker run -d -p 8080:8080 -v /var/run/docker.sock:/var/run/docker.sock:ro -v $PWD/config.ini:/app/config.ini registry/image:tag
```

### docker-compose

```bash
docker-compose up -d
```
