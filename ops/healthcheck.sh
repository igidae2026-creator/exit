#!/usr/bin/env bash
for s in $(systemctl list-units 'metaos@*' --no-legend | awk '{print $1}'); do
  systemctl is-active $s
done
df -h /var/lib/metaos || true
