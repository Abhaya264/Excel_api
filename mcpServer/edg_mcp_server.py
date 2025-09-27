#!/usr/bin/env python3
"""
EDGers Management MCP Server
An MCP server that provides tools to interact with EDGers scheduling and management data.
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin

import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.server.models import InitializationOptions
from mcp.types import (
    Resource,
    Tool,
    TextContent,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("edgers-mcp-server")

# Server configuration
BASE_URL = "http://127.0.0.1:5000"
SERVER_NAME = "edgers-management"
SERVER_VERSION = "1.0.0"


class EDGersServer:
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.http_client = httpx.AsyncClient(timeout=30.0)

    async def close(self):
        await self.http_client.aclose()

    async def make_api_request(self, endpoint: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """Make an API request to the EDGers service."""
        url = urljoin(self.base_url, endpoint)
        try:
            response = await self.http_client.get(url, params=params or {})
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"API request failed: {e}")
            raise Exception(f"API request failed: {str(e)}")

    async def get_edgers_by_role_and_date(self, date: str, role: str) -> List[Dict]:
        """Get EDGers by role and date."""
        endpoint = "/api/edgers"
        params = {"date": date, "role": role}
        return await self.make_api_request(endpoint, params)

    async def get_edger_schedule(self, edger_name: str) -> Dict:
        """Get schedule for a specific EDGer."""
        endpoint = f"/api/edgers/{edger_name}/schedule"
        return await self.make_api_request(endpoint)

    async def get_edgers_by_manager(self, manager_name: str) -> List[Dict]:
        """Get EDGers by manager."""
        endpoint = f"/api/managers/{manager_name}/edgers"
        return await self.make_api_request(endpoint)

    async def get_solo_salesforce_edgers(self) -> List[Dict]:
        """Get EDGers who are solo in Salesforce."""
        endpoint = "/api/edgers/solo-salesforce"
        return await self.make_api_request(endpoint)

    async def get_solo_ml_answers_edgers(self) -> List[Dict]:
        """Get EDGers who are solo in MATLAB Answers."""
        endpoint = "/api/edgers/solo-ml-answers"
        return await self.make_api_request(endpoint)


def create_server() -> Server:
    """Create and configure the MCP server."""
    server = Server(SERVER_NAME)
    edgers_server = EDGersServer()

    @server.list_tools()
    async def handle_list_tools() -> List[Tool]:
        """List available tools."""
        return [
            Tool(
                name="get_edgers_by_role_and_date",
                description="Get a list of EDGers assigned to a specific role on a given date",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "date": {
                            "type": "string",
                            "description": "Date in YYYY-MM-DD format"
                        },
                        "role": {
                            "type": "string",
                            "description": "Role name to filter by"
                        }
                    },
                    "required": ["date", "role"]
                }
            ),
            Tool(
                name="get_edger_schedule",
                description="Get the full schedule and details for a specific EDGer",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "edger_name": {
                            "type": "string",
                            "description": "Name of the EDGer to get schedule for"
                        }
                    },
                    "required": ["edger_name"]
                }
            ),
            Tool(
                name="get_edgers_by_manager",
                description="Get all EDGers who report to a specific manager",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "manager_name": {
                            "type": "string",
                            "description": "Name of the manager"
                        }
                    },
                    "required": ["manager_name"]
                }
            ),
            Tool(
                name="get_solo_salesforce_edgers",
                description="Get EDGers who are marked as solo in Salesforce ML Answers",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            ),
            Tool(
                name="get_solo_ml_answers_edgers",
                description="Get EDGers who are marked as solo in MATLAB Answers",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            )
        ]

    @server.call_tool()
    async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
        """Handle tool calls."""
        try:
            if name == "get_edgers_by_role_and_date":
                date = arguments.get("date")
                role = arguments.get("role")
                result = await edgers_server.get_edgers_by_role_and_date(date, role)
                
            elif name == "get_edger_schedule":
                edger_name = arguments.get("edger_name")
                result = await edgers_server.get_edger_schedule(edger_name)
                
            elif name == "get_edgers_by_manager":
                manager_name = arguments.get("manager_name")
                result = await edgers_server.get_edgers_by_manager(manager_name)
                
            elif name == "get_solo_salesforce_edgers":
                result = await edgers_server.get_solo_salesforce_edgers()
                
            elif name == "get_solo_ml_answers_edgers":
                result = await edgers_server.get_solo_ml_answers_edgers()
                
            else:
                raise ValueError(f"Unknown tool: {name}")

            return [TextContent(
                type="text",
                text=json.dumps(result, indent=2, default=str)
            )]
            
        except Exception as e:
            logger.error(f"Tool call failed: {e}")
            return [TextContent(
                type="text",
                text=f"Error: {str(e)}"
            )]

    @server.list_resources()
    async def handle_list_resources() -> List[Resource]:
        """List available resources."""
        return [
            Resource(
                uri="edgers://info",
                name="EDGers API Information",
                description="Information about the EDGers management system",
                mimeType="text/plain"
            )
        ]

    @server.read_resource()
    async def handle_read_resource(uri: str) -> str:
        """Handle resource reading."""
        if uri == "edgers://info":
            return """EDGers Management System API

Available endpoints:
- GET /api/edgers?date=YYYY-MM-DD&role=ROLE - Get EDGers by role and date
- GET /api/edgers/<edger_name>/schedule - Get schedule for specific EDGer  
- GET /api/managers/<manager_name>/edgers - Get EDGers by manager
- GET /api/edgers/solo-salesforce - Get solo Salesforce EDGers
- GET /api/edgers/solo-ml-answers - Get solo MATLAB Answers EDGers

This MCP server provides tools to interact with all these endpoints programmatically.
"""
        else:
            raise ValueError(f"Unknown resource: {uri}")

    return server


async def main():
    """Main entry point for the MCP server."""
    server = create_server()
    
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name=SERVER_NAME,
                server_version=SERVER_VERSION,
                capabilities={
                    "tools": {"listChanged": True},
                    "resources": {"subscribe": True, "listChanged": True}
                }
            )
        )


if __name__ == "__main__":
    asyncio.run(main())