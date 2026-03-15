#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DIST_DIR="${ROOT_DIR}/dist"
DELIVERY_DIR="${DIST_DIR}/delivery_materials"

PLATFORM="${PLATFORM:-linux/amd64}"
API_TAG="${API_TAG:-0.5.prod}"
WEB_TAG="${WEB_TAG:-0.5.prod}"
CRAWLER_TAG="${CRAWLER_TAG:-0.1.prod}"
ACR_REPO="${ACR_REPO:-registry.cn-beijing.aliyuncs.com/wyhy/mirrors}"
BUNDLE_NAME="${BUNDLE_NAME:-yuxi-offline-prod-$(date +%Y%m%d_%H%M%S)}"

BASE_COMPOSE="${ROOT_DIR}/docker-compose.remote.full.yml"
PACK_COMPOSE="${DIST_DIR}/${BUNDLE_NAME}.compose.yml"

log() {
  printf '[package-delivery] %s\n' "$*"
}

require_cmd() {
  local cmd="$1"
  if ! command -v "${cmd}" >/dev/null 2>&1; then
    echo "Missing required command: ${cmd}" >&2
    exit 1
  fi
}

require_cmd docker
require_cmd sed
require_cmd bash

if [[ ! -f "${BASE_COMPOSE}" ]]; then
  echo "compose file not found: ${BASE_COMPOSE}" >&2
  exit 1
fi

API_LOCAL="yuxi-api:${API_TAG}"
WEB_LOCAL="yuxi-web:${WEB_TAG}"
CRAWLER_LOCAL="yuxi-crawler:${CRAWLER_TAG}"

API_REMOTE="${ACR_REPO}:yuxi-api-${API_TAG}"
WEB_REMOTE="${ACR_REPO}:yuxi-web-${WEB_TAG}"
CRAWLER_REMOTE="${ACR_REPO}:yuxi-crawler-${CRAWLER_TAG}"

log "Build custom images for ${PLATFORM}"
docker buildx build --platform "${PLATFORM}" -f "${ROOT_DIR}/docker/api.Dockerfile" -t "${API_LOCAL}" --load "${ROOT_DIR}"
docker buildx build --platform "${PLATFORM}" -f "${ROOT_DIR}/docker/web.Dockerfile" --target production -t "${WEB_LOCAL}" --load "${ROOT_DIR}"
docker buildx build --platform "${PLATFORM}" -f "${ROOT_DIR}/docker/crawler.Dockerfile" -t "${CRAWLER_LOCAL}" --load "${ROOT_DIR}"

log "Tag custom images as production tags"
docker tag "${API_LOCAL}" "${API_REMOTE}"
docker tag "${WEB_LOCAL}" "${WEB_REMOTE}"
docker tag "${CRAWLER_LOCAL}" "${CRAWLER_REMOTE}"

log "Pull third-party images as ${PLATFORM}"
for img in \
  postgres:16 \
  redis:7-alpine \
  quay.io/coreos/etcd:v3.5.5 \
  minio/minio:RELEASE.2023-03-20T20-16-18Z \
  milvusdb/milvus:v2.5.6 \
  neo4j:5.26; do
  docker pull --platform "${PLATFORM}" "${img}" >/dev/null
done

log "Generate production compose file: ${PACK_COMPOSE}"
cp -f "${BASE_COMPOSE}" "${PACK_COMPOSE}"
sed -i '' "s|${ACR_REPO}:yuxi-api-[^\"[:space:]]*|${API_REMOTE}|g" "${PACK_COMPOSE}"
sed -i '' "s|${ACR_REPO}:yuxi-web-[^\"[:space:]]*|${WEB_REMOTE}|g" "${PACK_COMPOSE}"
sed -i '' "s|${ACR_REPO}:yuxi-crawler-[^\"[:space:]]*|${CRAWLER_REMOTE}|g" "${PACK_COMPOSE}"

log "Export offline bundle (${BUNDLE_NAME})"
(
  cd "${ROOT_DIR}"
  bash scripts/offline_bundle.sh export \
    --bundle-name "${BUNDLE_NAME}" \
    --compose-files "dist/${BUNDLE_NAME}.compose.yml" \
    --with-env yes \
    --target-platform "${PLATFORM}"
)

log "Sync delivery materials"
mkdir -p "${DELIVERY_DIR}/patches"
cp -f "${PACK_COMPOSE}" "${DELIVERY_DIR}/docker-compose.remote.full.yml"
cp -f "${ROOT_DIR}/scripts/offline_bundle.sh" "${DELIVERY_DIR}/offline_bundle.sh"
cp -f "${ROOT_DIR}/scripts/check_services.sh" "${DELIVERY_DIR}/check_services.sh"
cp -f "${ROOT_DIR}/scripts/fix_crawler_db_path.sh" "${DELIVERY_DIR}/fix_crawler_db_path.sh"
cp -f "${ROOT_DIR}/docs/离线交付部署说明.md" "${DELIVERY_DIR}/离线交付部署说明.md"
cp -f "${DIST_DIR}/${BUNDLE_NAME}.tar.gz" "${DELIVERY_DIR}/${BUNDLE_NAME}.tar.gz"
if [[ -f "${ROOT_DIR}/crawler_data/crawler.db" ]]; then
  cp -f "${ROOT_DIR}/crawler_data/crawler.db" "${DELIVERY_DIR}/patches/crawler.db"
  (cd "${DELIVERY_DIR}/patches" && tar -czf crawler-db-patch.tar.gz crawler.db && rm -f crawler.db)
fi

{
  shasum -a 256 "${DELIVERY_DIR}/${BUNDLE_NAME}.tar.gz"
  shasum -a 256 "${DELIVERY_DIR}/docker-compose.remote.full.yml"
  shasum -a 256 "${DELIVERY_DIR}/离线交付部署说明.md"
} > "${DELIVERY_DIR}/sha256sum.txt"

log "Done"
log "Bundle: ${DIST_DIR}/${BUNDLE_NAME}.tar.gz"
log "Delivery dir: ${DELIVERY_DIR}"
