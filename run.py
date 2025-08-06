#!/usr/bin/env python
"""Direct runner for GitBridge without installation"""

import os
import sys

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import and run the CLI
from gitbridge.cli import main

if __name__ == "__main__":
    main()
