#!/usr/bin/env bash

set -euo pipefail

bash .devcontainer/prepare-home.sh
bash .devcontainer/bootstrap-home.sh
bash .devcontainer/codex-config-init.sh
