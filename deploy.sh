#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="$SCRIPT_DIR/.env"
COMPOSE_FILE="$SCRIPT_DIR/compose.yaml"

if ! command -v docker >/dev/null 2>&1; then
  echo "Docker CLI not found. Start Docker Desktop and check PATH." >&2
  exit 1
fi

if [[ ! -f "$ENV_FILE" ]]; then
  echo "Missing .env. Copy .env.example to .env and set LAB_DB_PASSWORD." >&2
  exit 1
fi

compose=(docker compose --project-directory "$SCRIPT_DIR" --env-file "$ENV_FILE" -f "$COMPOSE_FILE")

echo "Validating Compose configuration..."
"${compose[@]}" config --quiet

echo "Building image and starting services..."
"${compose[@]}" up --build --detach

echo "Service status:"
"${compose[@]}" ps
