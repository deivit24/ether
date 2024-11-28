#!/bin/sh

echo "POSTGRES_HOST: $POSTGRES_HOST"
echo "POSTGRES_PORT: $POSTGRES_PORT"

# Ensure variables are not empty
if [ -z "$POSTGRES_HOST" ] || [ -z "$POSTGRES_PORT" ]; then
  echo "Error: POSTGRES_HOST or POSTGRES_PORT is not set!"
  exit 1
fi

echo "Waiting for postgres at $POSTGRES_HOST:$POSTGRES_PORT..."

# Health check loop to wait until Postgres is available
while ! nc -z "$POSTGRES_HOST" "$POSTGRES_PORT"; do
  sleep 0.1
done

echo "Postgres started at $POSTGRES_HOST:$POSTGRES_PORT"

# Upgrading alembic version
cd ..
alembic upgrade head

cd app

# Start the API
uvicorn main:app --reload --host 0.0.0.0 --port 8000
