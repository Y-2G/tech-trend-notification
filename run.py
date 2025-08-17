#!/usr/bin/env python3
"""
Entry point for Tech Trend Notifier
Handles proper Python path setup for imports
"""

import sys
import os
from pathlib import Path

# Add src directory to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

# Now import and run the main application
if __name__ == "__main__":
    from main import main
    import asyncio
    asyncio.run(main())