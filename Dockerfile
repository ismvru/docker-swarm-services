FROM python:3-slim
WORKDIR /app
COPY req.txt /app/
RUN pip --no-cache-dir install -r req.txt
COPY . /app/
ENV PATH ${PATH}:/app/
CMD ["start-service.sh"]