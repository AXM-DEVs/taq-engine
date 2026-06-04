#!/usr/bin/env bash
set -euo pipefail
APP="taq"; DIST="dist"
echo "=== TaQ Engine Build ==="
rm -rf "$DIST" build *.spec
if [ ! -d venv ]; then python3.12 -m venv venv; fi
source venv/bin/activate
pip install -q --upgrade pip setuptools wheel
pip install -q -r requirements.txt
pip install -q nuitka
mkdir -p "$DIST/playbooks"
cp playbooks/*.yaml "$DIST/playbooks/" 2>/dev/null || true
python -m nuitka --standalone --onefile --python-flag=no_docstrings --output-dir="$DIST" --output-file="$APP" --include-package=taq taq/main.py
echo "Binary: $DIST/$APP"
