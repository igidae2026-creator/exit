#!/usr/bin/env bash
DIR=/var/lib/metaos/shared_artifacts
find $DIR -type f -mtime +7 -delete
