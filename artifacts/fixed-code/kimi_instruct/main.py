#!/usr/bin/env python3
"""
Kimi Instruct Main Entry Point
"""

import asyncio
import sys

# Import the service module dynamically
module = importlib.import_module("kimi_instruct.service")

if __name__ == "__main__":
    asyncio.run(module.main())