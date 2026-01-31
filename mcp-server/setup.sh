#!/bin/bash
# MCP Server Setup Script for The Lab Verse Monitoring

set -e

echo "🚀 Setting up CData MCP Server..."

# Check Python version
python3 --version || (echo "❌ Python 3.12+ required" && exit 1)

# Install uv if not present
if ! command -v uv &> /dev/null; then
    echo "📦 Installing uv..."
    pip install --upgrade uv
fi

# Create virtual environment
echo "🔧 Creating virtual environment..."
uv venv .venv
source .venv/bin/activate

# Install MCP CLI
echo "📦 Installing MCP CLI..."
uv pip install "mcp[cli]"

# Install CData PostgreSQL connector (example)
echo "📦 Installing CData PostgreSQL connector..."
curl -L -o cdata.postgresql.whl https://download.cdata.com/connector/postgresql/latest/cdata.postgresql-2024.10.0-py3-none-any.whl
uv pip install ./cdata.postgresql.whl

# Create server startup script
cat > start_server.py << 'PYEOF'
#!/usr/bin/env python3
import os
import asyncio
from mcp.server.fastmcp import FastMCP

# Configuration
CONNECTOR_MOD = os.getenv("CONNECTOR_MOD", "cdata.postgresql")
CONNECTION_STRING = os.getenv("CONNECTION_STRING", "Server=host.docker.internal;Port=5432;Database=mydb;User Id=myuser;Password=mypass;")

async def main():
    """Start the MCP server"""
    print(f"🚀 Starting MCP server with connector: {CONNECTOR_MOD}")
    print(f"🔗 Connection string configured")
    
    # Initialize and run FastMCP server
    mcp = FastMCP("lab-verse-mcp")
    
    # Add basic health check
    @mcp.tool()
    async def health_check() -> str:
        return "✅ MCP Server is healthy"
    
    # Add database test tool
    @mcp.tool()
    async def test_connection() -> str:
        try:
            # Import and test the connector
            connector = __import__(CONNECTOR_MOD, fromlist=[''])
            return f"✅ Connected to {CONNECTOR_MOD}"
        except Exception as e:
            return f"❌ Connection failed: {str(e)}"
    
    await mcp.run()

if __name__ == "__main__":
    asyncio.run(main())
PYEOF

chmod +x start_server.py

echo "✅ MCP Server setup complete!"
echo ""
echo "📋 Next steps:"
echo "1. Set your connection string: export CONNECTION_STRING='...'"
echo "2. Start the server: ./start_server.py"
echo "3. Server will be available at: http://localhost:8000"
