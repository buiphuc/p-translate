#!/bin/bash
# Wrapper to launch QTranslate Linux and capture all errors
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
/usr/bin/python3 "$DIR/main.py" > "$DIR/error.log" 2>&1
