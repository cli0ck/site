#!/usr/bin/env bash
# cli0ck — local preview server. Nothing leaves this machine.
#   ./serve.sh          -> http://127.0.0.1:1337  (loopback only)
#   ./serve.sh 0.0.0.0  -> also reachable from the LAN / Windows host
set -euo pipefail
PORT="${PORT:-1337}"
BIND="${1:-127.0.0.1}"
cd "$(dirname "$0")"
echo "cli0ck -> http://${BIND}:${PORT}/   (ctrl+c to stop)"
exec python3 -m http.server "$PORT" --bind "$BIND" -d .
