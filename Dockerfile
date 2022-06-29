FROM python:3-slim
WORKDIR /app
COPY req.txt req-flask.txt req-fastapi.txt /app/
RUN pip --no-cache-dir install -r req.txt -r req-flask.txt -r req-fastapi.txt
COPY . /app/
ENV PATH ${PATH}:/app/
CMD ["start-service.sh", "fastapi"]