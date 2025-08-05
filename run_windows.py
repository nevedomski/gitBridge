#!/usr/bin/env python
"""Direct runner for GitSync on Windows with auto-detection"""

import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set default auto-detection flags for Windows
if len(sys.argv) == 1:
    print("GitSync - Windows Corporate Environment Helper")
    print("=" * 50)
    print("\nNo arguments provided. Running with auto-detection enabled.")
    print("\nUsage examples:")
    print("  python run_windows.py sync --repo https://github.com/user/repo --local C:\\repos\\project")
    print("  python run_windows.py sync --config config.yaml")
    print("  python run_windows.py init")
    print("\nFor this run, using: sync --help")
    sys.argv = ["run_windows.py", "sync", "--help"]
else:
    # If sync command is used without auto flags, add them
    if "sync" in sys.argv and not any(flag in sys.argv for flag in ["--auto-proxy", "--auto-cert", "--no-ssl-verify", "--help", "-h"]):
        print("Note: Auto-enabling proxy and certificate detection for Windows")
        sys.argv.extend(["--auto-proxy", "--auto-cert"])

# Import and run the CLI
from gitsync.cli import main

if __name__ == "__main__":
    main()