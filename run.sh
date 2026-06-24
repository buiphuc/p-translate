#!/bin/bash
# Wrapper to launch P-Translate and capture all errors
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="$HOME/.cache/p-translate"
mkdir -p "$LOG_DIR"
/usr/bin/python3 "$DIR/main.py" > "$LOG_DIR/error.log" 2>&1
