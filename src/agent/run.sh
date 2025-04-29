#!/bin/bash

# Run migrations first
alembic upgrade head &&
# Then start the application
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload