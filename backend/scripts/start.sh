#!/usr/bin/env bash
# Start the Tongye backend development server.
set -e

cd "$(dirname "$0")/.."

HOST="${HOST:-0.0.0.0}"
PORT="${PORT:-8000}"

echo "Starting Tongye backend on ${HOST}:${PORT} ..."
exec uvicorn app.main:app --host "${HOST}" --port "${PORT}" --reload
