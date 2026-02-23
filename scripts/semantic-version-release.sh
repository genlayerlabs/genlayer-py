#!/bin/bash
set -euo pipefail

# Script to check if a new semantic release is needed
# Outputs GitHub Actions outputs for use in workflows

CONFIG_FILE="${1:-releaserc.toml}"
GITHUB_OUTPUT="${GITHUB_OUTPUT:-/dev/stdout}"

echo "Checking for new release using config: $CONFIG_FILE"


# Run semantic-release version with selective error handling
# Exit code 0: release created, 1: no release needed, >1: genuine error
set +e
RELEASE_OUTPUT=$(uvx --from 'python-semantic-release==10.0.2' semantic-release -c "$CONFIG_FILE" -vv version 2>&1)
RC=$?
set -e

if [[ $RC -gt 1 ]]; then
  echo "Error: semantic-release failed with exit code $RC" >&2
  exit $RC
fi

echo "$RELEASE_OUTPUT"


# Check if no release will be made
if echo "$RELEASE_OUTPUT" | grep -qi "No release will be made"; then
    echo "released=false" >> "$GITHUB_OUTPUT"
elif echo "$RELEASE_OUTPUT" | grep -qi "Failed to create release"; then
    echo "released=false" >> "$GITHUB_OUTPUT"
else
    echo "released=true" >> "$GITHUB_OUTPUT"
fi 