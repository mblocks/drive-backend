FROM tiangolo/uvicorn-gunicorn-fastapi:python3.8-slim
ADD requirements.txt /app
RUN pip install -r requirements.txt --no-cache-dir
COPY . /app
VOLUME ["/drive"]
