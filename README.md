# Drive Backend

Mblocks Drive Backend

## Run

```bash

pipenv shell

# initial database
python scripts/initial_database.py
python scripts/initial_data.py
python scripts/initial_minio.py
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
