#!/bin/bash
set -e

echo "🚀 Custom build script - forcing pip usage"
echo "Current directory: $(pwd)"
echo "Python version: $(python --version)"
echo "Pip version: $(pip --version)"

echo "📦 Installing dependencies with pip..."
pip install --upgrade pip
pip install -r requirements.txt

echo "✅ Build completed successfully!"
echo "📋 Installed packages:"
pip list | head -10