#!/usr/bin/env bash
# 3D Model Review 起動スクリプト
#
#   bash viewer/start.sh                  # カレントディレクトリのワークスペースを開く
#   bash viewer/start.sh /path/to/project # 指定ディレクトリのワークスペースを開く
#   bash viewer/start.sh --models ./out   # STL のあるディレクトリを直接開く
#
# 追加の引数はそのまま server.py に渡る（--port など）。
# ポートは 8765 から空きを自動探索する。他プロセスは kill しない。
set -euo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PY="${PYTHON:-python3}"

if ! command -v "$PY" >/dev/null 2>&1; then
  echo "python3 が見つかりません。Python 3.10 以上を入れてください（PYTHON=... で上書き可）。" >&2
  exit 1
fi

# 第1引数がオプションでなければ、作業ディレクトリ指定として扱う
ARGS=()
if [ $# -gt 0 ] && [ "${1#-}" = "$1" ]; then
  ARGS+=(--workspace "$1")
  shift
fi
ARGS+=("$@")

PORT_FILE="${MODEL_REVIEW_HOME:-$HOME/.model-review}/port"
rm -f "$PORT_FILE"

"$PY" "$DIR/server.py" "${ARGS[@]}" &
SERVER_PID=$!
trap 'kill "$SERVER_PID" 2>/dev/null || true' INT TERM

# ポートファイルが書かれたらブラウザを開く
for _ in $(seq 1 30); do
  if [ -f "$PORT_FILE" ]; then
    URL="http://localhost:$(cat "$PORT_FILE")"
    if [ -d "/Applications/Google Chrome.app" ]; then
      open -a "Google Chrome" "$URL"
    elif command -v open >/dev/null 2>&1; then
      open "$URL"
    elif command -v xdg-open >/dev/null 2>&1; then
      xdg-open "$URL"
    fi
    break
  fi
  sleep 0.3
done

wait "$SERVER_PID"
