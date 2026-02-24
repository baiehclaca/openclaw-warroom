#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

PROFILE="${WARROOM_PROFILE:-default}"
LINK_ID="${WARROOM_LINK:-local}"
LIVE_FEED="${WARROOM_LIVE_FEED:-0}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --profile)
      PROFILE="$2"
      shift 2
      ;;
    --link|--link-id)
      LINK_ID="$2"
      shift 2
      ;;
    --live-feed)
      LIVE_FEED="1"
      shift 1
      ;;
    *)
      echo "Unknown arg: $1"
      echo "Usage: ./run-warroom.sh [--profile <name>] [--link <id>] [--live-feed]"
      exit 1
      ;;
  esac
done

if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 is required"
  exit 1
fi

if [[ ! -d ".venv" ]]; then
  python3 -m venv .venv
fi

source .venv/bin/activate
export PIP_DISABLE_PIP_VERSION_CHECK=1
export PIP_NO_CACHE_DIR=1
pip install --disable-pip-version-check --no-cache-dir -q -r requirements.txt

export WARROOM_PROFILE="$PROFILE"
export WARROOM_LINK="$LINK_ID"
export WARROOM_LIVE_FEED="$LIVE_FEED"

exec python3 warroom.py
