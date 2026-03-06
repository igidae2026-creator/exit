#!/usr/bin/env bash
set -e
CORES=$(nproc)
for ((i=0;i<CORES;i++)); do
  systemctl enable --now metaos@$i.service
done
