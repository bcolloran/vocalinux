#!/usr/bin/env bash

set -euo pipefail

bash .devcontainer/prepare-home.sh
bash .devcontainer/bootstrap-home.sh

cd /workspaces/vocalinux

bash .devcontainer/codex-config-init.sh
pip install -e ".[dev]"
