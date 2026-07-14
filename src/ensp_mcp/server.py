"""MCP Server — 组装 MCP 服务、注册 list_tools / call_tool 回调。"""

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from .tools import TOOLS, dispatch

server = Server("ensp-mcp")


@server.list_tools()
async def list_tools() -> list[Tool]:
    return TOOLS


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    return await dispatch(name, arguments)


async def run():
    """启动 MCP 服务（stdio 传输）。"""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())
