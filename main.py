#!/usr/bin/env python3
"""
Render deployment entry point
Redirects to the actual application
"""

# Import the actual FastAPI app from real_sentinel_api
from real_sentinel_api import app

# This allows Render to use 'main:app' while actually running our real API
__all__ = ['app']