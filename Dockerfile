FROM tiangolo/uvicorn-gunicorn-fastapi:python3.8

WORKDIR /app/

COPY . /app
ENV PYTHONPATH=/app

RUN pip install -r requirements.txt --no-cache-dir
