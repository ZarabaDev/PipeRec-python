#!/usr/bin/env python3
"""
PipeRec - Dual Audio Capture
Main entry point.
"""

import os
import sys

# Ensure we're in the right directory
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the main GUI application
from src.gui.app import main

if __name__ == "__main__":
    print("🚀 PipeRec starting...")
    main()
