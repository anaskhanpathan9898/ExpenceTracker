"""
api/index.py
------------
Serverless function entrypoint for Vercel deployment.
Exposes the Flask WSGI application instance.
"""

import os
import sys

# Add project root directory to sys.path so root packages (models, routes, config, app) resolve properly
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from app import app
