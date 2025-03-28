import asyncio
import os
from datetime import datetime, date
from typing import Optional, List, Dict, Any, Union

from mcp.server.models import InitializationOptions
import mcp.types as types
from mcp.server import NotificationOptions, Server
from pydantic import AnyUrl, BaseModel, Field
import mcp.server.stdio
from polygon import RESTClient

# Get API key from environment variables
POLYGON_API_KEY = os.environ.get("POLYGON_API_KEY", "")
if not POLYGON_API_KEY:
    print("Warning: POLYGON_API_KEY environment variable not set.")

# Initialize Polygon client
polygon_client = RESTClient(POLYGON_API_KEY)

# Store notes as a simple key-value dict to demonstrate state management
notes: dict[str, str] = {}

server = Server("mcp_polygon")

@server.list_resources()
async def handle_list_resources() -> list[types.Resource]:
    """
    List available note resources.
    Each note is exposed as a resource with a custom note:// URI scheme.
    """
    return [
        types.Resource(
            uri=AnyUrl(f"note://internal/{name}"),
            name=f"Note: {name}",
            description=f"A simple note named {name}",
            mimeType="text/plain",
        )
        for name in notes
    ]

@server.read_resource()
async def handle_read_resource(uri: AnyUrl) -> str:
    """
    Read a specific note's content by its URI.
    The note name is extracted from the URI host component.
    """
    if uri.scheme != "note":
        raise ValueError(f"Unsupported URI scheme: {uri.scheme}")

    name = uri.path
    if name is not None:
        name = name.lstrip("/")
        return notes[name]
    raise ValueError(f"Note not found: {name}")

@server.list_prompts()
async def handle_list_prompts() -> list[types.Prompt]:
    """
    List available prompts.
    Each prompt can have optional arguments to customize its behavior.
    """
    return [
        types.Prompt(
            name="summarize-notes",
            description="Creates a summary of all notes",
            arguments=[
                types.PromptArgument(
                    name="style",
                    description="Style of the summary (brief/detailed)",
                    required=False,
                )
            ],
        )
    ]

@server.get_prompt()
async def handle_get_prompt(
    name: str, arguments: dict[str, str] | None
) -> types.GetPromptResult:
    """
    Generate a prompt by combining arguments with server state.
    The prompt includes all current notes and can be customized via arguments.
    """
    if name != "summarize-notes":
        raise ValueError(f"Unknown prompt: {name}")

    style = (arguments or {}).get("style", "brief")
    detail_prompt = " Give extensive details." if style == "detailed" else ""

    return types.GetPromptResult(
        description="Summarize the current notes",
        messages=[
            types.PromptMessage(
                role="user",
                content=types.TextContent(
                    type="text",
                    text=f"Here are the current notes to summarize:{detail_prompt}\n\n"
                    + "\n".join(
                        f"- {name}: {content}"
                        for name, content in notes.items()
                    ),
                ),
            )
        ],
    )

@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """
    List available tools.
    Each tool specifies its arguments using JSON Schema validation.
    """
    return [
        types.Tool(
            name="add-note",
            description="Add a new note",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "content": {"type": "string"},
                },
                "required": ["name", "content"],
            },
        ),
        types.Tool(
            name="get-aggs",
            description="Get aggregated stock data from Polygon.io",
            inputSchema={
                "type": "object",
                "properties": {
                    "ticker": {"type": "string", "description": "Stock ticker symbol (e.g., AAPL)"},
                    "multiplier": {"type": "integer", "description": "Size of the timespan multiplier", "default": 1},
                    "timespan": {
                        "type": "string", 
                        "description": "Size of the time window", 
                        "enum": ["minute", "hour", "day", "week", "month", "quarter", "year"],
                        "default": "day"
                    },
                    "from_date": {"type": "string", "description": "From date in YYYY-MM-DD format"},
                    "to_date": {"type": "string", "description": "To date in YYYY-MM-DD format"},
                    "limit": {"type": "integer", "description": "Limit of results returned", "default": 10},
                },
                "required": ["ticker", "from_date", "to_date"],
            },
        ),
        types.Tool(
            name="get-trades",
            description="Get historical trades for a ticker from Polygon.io",
            inputSchema={
                "type": "object",
                "properties": {
                    "ticker": {"type": "string", "description": "Stock ticker symbol (e.g., AAPL)"},
                    "date": {"type": "string", "description": "Date for the trades in YYYY-MM-DD format"},
                    "timestamp": {"type": "integer", "description": "Timestamp in Unix milliseconds format", "default": 0},
                    "limit": {"type": "integer", "description": "Limit of results returned", "default": 10},
                },
                "required": ["ticker", "date"],
            },
        )
    ]

async def handle_add_note(arguments: dict) -> list[types.TextContent]:
    """
    Add a new note to the server.
    
    Args:
        arguments: Dictionary containing note name and content
        
    Returns:
        List of TextContent with operation result
    """
    note_name = arguments.get("name")
    content = arguments.get("content")

    if not note_name or not content:
        raise ValueError("Missing name or content")

    # Update server state
    notes[note_name] = content

    # Notify clients that resources have changed
    await server.request_context.session.send_resource_list_changed()

    return [
        types.TextContent(
            type="text",
            text=f"Added note '{note_name}' with content: {content}",
        )
    ]

async def handle_get_aggs(arguments: dict) -> list[types.TextContent]:
    """
    Get aggregated stock data from Polygon API.
    
    Args:
        arguments: Dictionary containing query parameters
        
    Returns:
        List of TextContent with aggregated data or error message
    """
    if not POLYGON_API_KEY:
        return [
            types.TextContent(
                type="text",
                text="Error: Polygon API key not set. Please set the POLYGON_API_KEY environment variable."
            )
        ]

    ticker = arguments.get("ticker")
    multiplier = arguments.get("multiplier", 1)
    timespan = arguments.get("timespan", "day")
    from_ = arguments.get("from")
    to = arguments.get("to")
    limit = arguments.get("limit", 10)
    
    if not ticker or not from_ or not to or not timespan or not multiplier:
        raise ValueError("Missing required parameters: ticker, from_, or to")
    
    try:
        # Call Polygon API
        results = polygon_client.get_aggs(
            ticker=ticker,
            multiplier=multiplier,
            timespan=timespan,
            from_=from_,
            to=to,
            limit=limit
        )

        response_text = f"Aggregated data for {ticker} from {from_} to {to}:\n\n"
        response_text += f"Found {len(results)} results\n\n"
        
        # Include the first few results in the text response
        if results:
            for i, result in enumerate(results[:5]):
                response_text += f"Entry {i+1}:\n"
                for key, value in result.items():
                    if value is not None:
                        response_text += f"  {key}: {value}\n"
                response_text += "\n"
            
            if len(results) > 5:
                response_text += f"...and {len(results) - 5} more entries."
        else:
            response_text += "No results found."
        
        return [
            types.TextContent(
                type="text",
                text=response_text
            )
        ]
    except Exception as e:
        return [
            types.TextContent(
                type="text",
                text=f"Error fetching aggregated data: {str(e)}"
            )
        ]

async def handle_list_trades(arguments: dict) -> list[types.TextContent]:
    """
    Get historical trade data from Polygon API.
    
    Args:
        arguments: Dictionary containing query parameters
        
    Returns:
        List of TextContent with trade data or error message
    """
    if not POLYGON_API_KEY:
        return [
            types.TextContent(
                type="text",
                text="Error: Polygon API key not set. Please set the POLYGON_API_KEY environment variable."
            )
        ]

    ticker = arguments.get("ticker")
    
    if not ticker:
        raise ValueError("Missing required parameters: ticker or date")
    
    limit = arguments.get("limit", 100)
    try:
        # Call Polygon API
        results = polygon_client.list_trades(
            ticker=ticker,
            timestamp_gte=arguments.get("timestamp.gte", None),
            timestamp_gt=arguments.get("timestamp.gt", None),
            timestamp_lte=arguments.get("timestamp.lte", None),
            timestamp_lt=arguments.get("timestamp.lt", None),
            order="asc",
            sort=arguments.get("sort", "asc"),
            limit=limit,
        )
        
        response_text = f"Trade data for {ticker}:\n\n"

        # Include the first few results in the text response
        if results:
            for i, result in enumerate(results):
                if i >= limit:
                    break
                response_text += f"Trade {i+1}:\n {result}\n"

        else:
            response_text += "No trade data found."
        
        return [
            types.TextContent(
                type="text",
                text=response_text
            )
        ]
    except Exception as e:
        return [
            types.TextContent(
                type="text",
                text=f"Error fetching trade data: {str(e)}"
            )
        ]

@server.call_tool()
async def handle_call_tool(
    name: str, arguments: dict | None
) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    """
    Handle tool execution requests.
    Dispatches to appropriate handler function based on tool name.
    """
    if not arguments:
        raise ValueError("Missing arguments")

    # Dispatch to the appropriate handler based on tool name
    if name == "add-note":
        return await handle_add_note(arguments)
    elif name == "get-aggs":
        return await handle_get_aggs(arguments)
    elif name == "get-trades":
        return await handle_list_trades(arguments)
    else:
        raise ValueError(f"Unknown tool: {name}")

async def main():
    # Run the server using stdin/stdout streams
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="mcp_polygon",
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )
