#!/usr/bin/env bash

set -euo pipefail

HOST_HOME_ROOT="${HOST_HOME_ROOT:-/host-home}"

sync_dir() {
  local src="$1"
  local dest="$2"

  if [ ! -d "${src}" ]; then
    return 0
  fi

  mkdir -p "${dest}"
  rsync -a --update "${src}/" "${dest}/"
}

sync_file() {
  local src="$1"
  local dest="$2"

  if [ ! -f "${src}" ]; then
    return 0
  fi

  mkdir -p "$(dirname "${dest}")"

  if [ ! -f "${dest}" ] || [ "${src}" -nt "${dest}" ]; then
    install -m 600 "${src}" "${dest}"
  fi
}

sync_dir "${HOST_HOME_ROOT}/.codex" "${HOME}/.codex"
sync_dir "${HOST_HOME_ROOT}/.claude" "${HOME}/.claude"
sync_dir "${HOST_HOME_ROOT}/.config/gh" "${HOME}/.config/gh"
sync_dir "${HOST_HOME_ROOT}/.config/Code/User/snippets" "${HOME}/.config/Code/User/snippets"
sync_dir "${HOST_HOME_ROOT}/.config/Code/User/globalStorage" "${HOME}/.vscode-server/data/User/globalStorage"

sync_file "${HOST_HOME_ROOT}/.gitconfig" "${HOME}/.gitconfig"
sync_file "${HOST_HOME_ROOT}/.config/pulse/cookie" "${HOME}/.config/pulse/cookie"
sync_file "${HOST_HOME_ROOT}/.config/Code/User/settings.json" "${HOME}/.vscode-server/data/Machine/settings.json"
sync_file "${HOST_HOME_ROOT}/.config/Code/User/keybindings.json" "${HOME}/.config/Code/User/keybindings.json"
