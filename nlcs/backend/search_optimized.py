# Optimized Search Engine with Batching Strategy
# Handles token limits while maintaining accuracy and speed

import json
import time
import sys
import os
from pathlib import Path
from sqlalchemy.orm import Session
from dotenv import load_dotenv

# Handle import paths
current_dir = Path(__file__).parent
parent_dir = current_dir.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))
"""Compatibility wrapper for the current search module."""

from search import *  # noqa: F401,F403
try:
