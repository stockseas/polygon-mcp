# Polygon.io MCP Server

A [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) server that provides access to [Polygon.io](https://polygon.io) financial market data API through an LLM-friendly interface.

## Overview

This server exposes all Polygon.io API endpoints as MCP tools, providing access to comprehensive financial market data including:

- Stock, options, forex, and crypto aggregates and bars
- Real-time and historical trades and quotes
- Market snapshots
- Ticker details and reference data
- Dividends and splits data
- Financial fundamentals
- Market status and holidays

## Installation

### Prerequisites

- Python 3.8+
- A Polygon.io API key ([Get one here](https://polygon.io))

### Direct Installation

```bash
# Install dependencies
uv sync

# Run the server
POLYGON_API_KEY=your_api_key_here uv run mcp_polygon
```

### Integration with Claude

For Claude users, you can add the Polygon MCP server:

```bash
# Claude CLI
claude mcp add polygon -e POLYGON_API_KEY=your_api_key_here -- uv run /path/to/mcp_polygon/entrypoint.py
```

## Usage Examples

Once integrated, you can prompt Claude to access Polygon.io data:

```
Get the latest price for AAPL stock
Show me yesterday's trading volume for MSFT
What were the biggest stock market gainers today?
Get me the latest crypto market data for BTC-USD
```

## Available Tools

This MCP server implements all Polygon.io API endpoints as tools, including:

- `get_aggs` - Stock aggregates (OHLC) data for a specific ticker
- `list_trades` - Historical trade data
- `get_last_trade` - Latest trade for a symbol
- `list_ticker_news` - Recent news articles for tickers
- `get_snapshot_ticker` - Current market snapshot for a ticker
- `get_market_status` - Current market status and trading hours
- `list_stock_financials` - Fundamental financial data
- And many more...

Each tool follows the Polygon.io SDK parameter structure while converting responses to standard JSON that LLMs can easily process.

## Configuration

### Environment Variables

- `POLYGON_API_KEY` (required): Your Polygon.io API key

## Development

### Building and Publishing

```bash
# Sync dependencies
uv sync

# Build package distributions
uv build
```

### Debugging

For debugging and testing, we recommend using the [MCP Inspector](https://github.com/modelcontextprotocol/inspector):

```bash
npx @modelcontextprotocol/inspector uv --directory /path/to/mcp_polygon run mcp_polygon
```

This will launch a browser interface where you can interact with your MCP server directly and see input/output for each tool.

## License

[License information]

## Links

- [Polygon.io Documentation](https://polygon.io/docs)
- [Model Context Protocol](https://modelcontextprotocol.io)
- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
