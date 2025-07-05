#!/usr/bin/env python3
"""
Productivity Agent Runner - Entry point for the productivity tracking system
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from main import main

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nAgent stopped by user")
        sys.exit(0)
    except Exception as e:
        print(f"Agent failed to start: {e}")
        sys.exit(1)