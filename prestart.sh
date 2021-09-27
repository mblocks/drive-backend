#! /usr/bin/env sh

# create the path for sqlite data
python scripts/initial_database.py
python scripts/initial_data.py
python scripts/initial_minio.py
