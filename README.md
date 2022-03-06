# Drive Backend

Mblocks Drive Backend

## Run

```bash

pipenv shell
# prepare minio
docker run -d -p 9000:9000 -e MINIO_ROOT_USER=hello -e MINIO_ROOT_PASSWORD=helloworld -e MINIO_NOTIFY_WEBHOOK_ENABLE_DRIVE=on -e MINIO_NOTIFY_WEBHOOK_ENDPOINT_DRIVE=http://your-ip-port/webhooks/minio minio/minio server /data

# initial database
python scripts/initial_database.py
python scripts/initial_data.py
uvicorn app.main:app --reload

```

## Generate Requirement

```bash

pipenv lock -r > requirements.txt

```

## Test

```bash

pytest

```
