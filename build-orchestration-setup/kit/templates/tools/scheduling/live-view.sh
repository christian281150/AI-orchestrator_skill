#!/bin/sh
# Writes and opens a local status page that refreshes every 30 s. Read-only. Ctrl+C to stop.
cd "$(dirname "$0")/../.." || exit 1
OUT="${TMPDIR:-/tmp}/{{PROJECT_NAME}}-live-view.html"
python3 tools/orch.py --config orchestration.toml live-view --out "$OUT" >/dev/null
(command -v open >/dev/null && open "$OUT") || (command -v xdg-open >/dev/null && xdg-open "$OUT") || echo "open $OUT"
while true; do sleep 30; python3 tools/orch.py --config orchestration.toml live-view --out "$OUT" >/dev/null; done
