#!/usr/bin/env bash
set -euo pipefail
cd /home/meta_os/metaos
export PYTHONDONTWRITEBYTECODE=1
python3 scripts/run_threshold_autonomy_loop.py
