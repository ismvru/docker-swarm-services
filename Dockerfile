FROM python:3-slim
WORKDIR /app
COPY req.txt ./
RUN pip --no-cache-dir install -r req.txt
COPY main.py ./
CMD ["python3", "main.py"]