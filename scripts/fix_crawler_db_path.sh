#!/usr/bin/env bash
set -euo pipefail

COMPOSE_FILE="${1:-docker-compose.remote.full.yml}"

echo "[fix-crawler-db] using compose file: ${COMPOSE_FILE}"

docker compose -f "${COMPOSE_FILE}" exec -T crawler sh -lc '
set -e
mkdir -p /app/data

if [ ! -f /app/data/crawler.db ]; then
  touch /app/data/crawler.db
fi

DATA_SIZE=$(wc -c < /app/data/crawler.db || echo 0)
OLD_SIZE=0
if [ -f /app/crawler.db ]; then
  OLD_SIZE=$(wc -c < /app/crawler.db || echo 0)
fi

echo "[fix-crawler-db] /app/data/crawler.db size=${DATA_SIZE}"
echo "[fix-crawler-db] /app/crawler.db size=${OLD_SIZE}"

if [ "${OLD_SIZE}" -gt "${DATA_SIZE}" ]; then
  cp -f /app/data/crawler.db /app/data/crawler.db.bak.$(date +%Y%m%d_%H%M%S) || true
  cp -f /app/crawler.db /app/data/crawler.db
  echo "[fix-crawler-db] restored /app/data/crawler.db from /app/crawler.db"
else
  echo "[fix-crawler-db] skip restore (mounted db is newer or equal)"
fi
'

docker compose -f "${COMPOSE_FILE}" restart crawler crawler-worker

sleep 3
echo "[fix-crawler-db] health:"
curl -sS --max-time 10 http://127.0.0.1/crawler-api/health || true
echo
echo "[fix-crawler-db] tasks:"
curl -sS --max-time 10 'http://127.0.0.1/crawler-api/tasks?page=1&size=5' || true
echo

