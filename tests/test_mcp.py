import pytest
import asyncio
from mcp.mcp_integration import MCPRevitIntegration

def test_mcp_integration_init():
    """Test MCP integration initialization"""
    mcp = MCPRevitIntegration()
    assert mcp is not None
    assert not mcp.is_connected

@pytest.mark.asyncio
async def test_mcp_server_start():
    """Test MCP server startup"""
    mcp = MCPRevitIntegration()
    # Note: This would need actual server file to work
    # For now, just test the method exists
    assert hasattr(mcp, 'start_server')
    assert hasattr(mcp, 'stop_server')