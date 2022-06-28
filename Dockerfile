FROM python:3-slim
WORKDIR /app
COPY req.txt ./
RUN pip --no-cache-dir install -r req.txt
COPY static /app/static
COPY templates /app/templates
COPY serviceslister /app/serviceslister
COPY main.py /app/
CMD ["python3", "main.py"]