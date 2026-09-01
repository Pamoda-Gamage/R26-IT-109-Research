#!/bin/sh
set -e

echo "[entrypoint] running prerequisite bootstrap (idempotent -- skips anything already done)"
python -m app.scripts.bootstrap

echo "[entrypoint] starting: $*"
exec "$@"
