#!/bin/bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"

# 인스턴스 목록(필요하면 A B C D 늘려도 됨)
INSTANCES=("A" "B" "C")

# tmux 없으면 설치 권장
command -v tmux >/dev/null 2>&1 || { echo "tmux not found. Install: sudo apt install tmux -y"; exit 1; }

tmux has-session -t metaos-swarm 2>/dev/null && tmux kill-session -t metaos-swarm || true
tmux new-session -d -s metaos-swarm -n A

# 각 인스턴스 준비 + 실행
for i in "${!INSTANCES[@]}"; do
  inst="${INSTANCES[$i]}"
  "$ROOT/ops/rotate-instance.sh" "$inst" >/dev/null
  if [ "$i" -eq 0 ]; then
    tmux send-keys -t metaos-swarm:A "export METAOS_INSTANCE=$inst; cd \"$ROOT/instances/$inst\" && python3 -m core.autonomous_daemon" C-m
  else
    tmux new-window -t metaos-swarm -n "$inst"
    tmux send-keys -t "metaos-swarm:$inst" "export METAOS_INSTANCE=$inst; cd \"$ROOT/instances/$inst\" && python3 -m core.autonomous_daemon" C-m
  fi
done

echo "OK: running instances in tmux session: metaos-swarm"
echo "Attach: tmux attach -t metaos-swarm"
