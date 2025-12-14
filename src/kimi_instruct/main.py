#!/usr/bin/env python3
"""
Kimi Instruct Main Entry Point
"""

import asyncio
import sys
from pathlib import Path

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from kimi_instruct.service import main

if __name__ == "__main__":
    asyncio.run(main())