#!/usr/bin/env bash

set -euo pipefail

CODEX_HOME="${HOME}/.codex"
CONFIG_PATH="${CODEX_HOME}/config.toml"

mkdir -p "${CODEX_HOME}"

if grep -Eq '^[[:space:]]*cli_auth_credentials_store[[:space:]]*=' "${CONFIG_PATH}" 2>/dev/null; then
  exit 0
fi

if [ -f "${CONFIG_PATH}" ] && [ -s "${CONFIG_PATH}" ]; then
  printf '\ncli_auth_credentials_store = "file"\n' >> "${CONFIG_PATH}"
else
  printf 'cli_auth_credentials_store = "file"\n' > "${CONFIG_PATH}"
fi
