#! /bin/bash
# shellcheck shell=bash
set -euo pipefail

# dump data from a local database for testing purposes
# e.g. scripts/dumpdata.sh > data.json
manage dumpdata \
| jq 'map(select((.model != "authtoken.token") and (.model != "auth.permission") and (.model != "auth.group") and (.model != "sessions.session") and (.model != "contenttypes.contenttype")))'
