#!/usr/bin/env bash
set -e
INSTANCE_ID=$1
APP=/opt/metaos/app
VENV=/opt/metaos/venv
STATE=/var/lib/metaos/instances/instance-$INSTANCE_ID
ART=/var/lib/metaos/shared_artifacts
LOG=/var/log/metaos/instance-$INSTANCE_ID
mkdir -p $STATE $ART $LOG
export METAOS_APP_DIR=$APP
export METAOS_INSTANCE_DIR=$STATE
export METAOS_SHARED_ARTIFACTS_DIR=$ART
export METAOS_LOG_DIR=$LOG
cd $APP
exec $VENV/bin/python -m core.autonomous_daemon
