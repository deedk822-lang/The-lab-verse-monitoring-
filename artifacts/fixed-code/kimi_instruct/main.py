#!/usr/bin/env python3
"""
Kimi Instruct Main Entry Point
"""

import asyncio
import sys
from pathlib import Path

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

def main():
    try:
        # Assume this is a function from kimi_instruct.service module
        return kimi_instruct.service.main()
    except Exception as e:
        print(f"An error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())