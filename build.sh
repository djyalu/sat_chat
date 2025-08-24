#!/usr/bin/env bash
# Render build script

set -e

echo "=== Render Build Script Starting ==="
echo "Python version:"
python --version

echo "Installing pip dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo "=== Build completed successfully ==="
