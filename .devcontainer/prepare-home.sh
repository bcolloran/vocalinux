#!/usr/bin/env bash

set -euo pipefail

sudo mkdir -p \
  /home/vscode/.cache/pip \
  /home/vscode/.claude \
  /home/vscode/.codex \
  /home/vscode/.config/Code/User/snippets \
  /home/vscode/.config/gh \
  /home/vscode/.config/pulse \
  /home/vscode/.local/share \
  /home/vscode/.npm \
  /home/vscode/.vscode-server/data/Machine \
  /home/vscode/.vscode-server/data/User/globalStorage

sudo chown -R vscode:vscode \
  /home/vscode/.cache/pip \
  /home/vscode/.claude \
  /home/vscode/.codex \
  /home/vscode/.config/Code \
  /home/vscode/.config/gh \
  /home/vscode/.config/pulse \
  /home/vscode/.local/share \
  /home/vscode/.npm \
  /home/vscode/.vscode-server
