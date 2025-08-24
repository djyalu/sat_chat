#!/usr/bin/env python3
"""Test script to verify all imports work correctly"""

import sys
print(f"Python version: {sys.version}")

try:
    import fastapi
    print(f"✅ FastAPI: {fastapi.__version__}")
except ImportError as e:
    print(f"❌ FastAPI import failed: {e}")

try:
    import uvicorn
    print(f"✅ Uvicorn imported successfully")
except ImportError as e:
    print(f"❌ Uvicorn import failed: {e}")

try:
    import dotenv
    print(f"✅ Python-dotenv imported successfully")
except ImportError as e:
    print(f"❌ Python-dotenv import failed: {e}")

try:
    import sentinelhub
    print(f"✅ Sentinelhub: {sentinelhub.__version__}")
except ImportError as e:
    print(f"❌ Sentinelhub import failed: {e}")

try:
    import numpy as np
    print(f"✅ NumPy: {np.__version__}")
except ImportError as e:
    print(f"❌ NumPy import failed: {e}")

try:
    import PIL
    print(f"✅ Pillow: {PIL.__version__}")
except ImportError as e:
    print(f"❌ Pillow import failed: {e}")

try:
    import matplotlib
    print(f"✅ Matplotlib: {matplotlib.__version__}")
except ImportError as e:
    print(f"❌ Matplotlib import failed: {e}")

try:
    import requests
    print(f"✅ Requests: {requests.__version__}")
except ImportError as e:
    print(f"❌ Requests import failed: {e}")

try:
    import httpx
    print(f"✅ HTTPX: {httpx.__version__}")
except ImportError as e:
    print(f"❌ HTTPX import failed: {e}")

try:
    import scipy
    print(f"✅ SciPy: {scipy.__version__}")
except ImportError as e:
    print(f"❌ SciPy import failed: {e}")

print("\nImport test completed!")