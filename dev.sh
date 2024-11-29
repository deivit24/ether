#!/bin/bash

# Determine which environment to use
if [ "$1" = "build" ]; then
docker compose down -v; docker compose up --build
elif [ "$1" = "d" ]; then
  docker compose down -v; docker compose up -d
else
  echo "Invalid environment: $1. Use 'b' for build or 'd' for detached"
fi