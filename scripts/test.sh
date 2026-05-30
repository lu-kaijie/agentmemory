#!/usr/bin/env bash
set -euo pipefail

uv run pytest
uv run openspec validate --all --strict
