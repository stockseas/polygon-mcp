# mcp_polygon MCP server

A MCP server project that provides access to Polygon.io financial market data through the MCP protocol.

## Components

### Resources

The server implements a simple note storage system with:
- Custom note:// URI scheme for accessing individual notes
- Each note resource has a name, description and text/plain mimetype

### Prompts

The server provides a single prompt:
- summarize-notes: Creates summaries of all stored notes
  - Optional "style" argument to control detail level (brief/detailed)
  - Generates prompt combining all current notes with style preference

### Tools

The server implements the following tools:

1. Note Management:
   - add-note: Adds a new note to the server
     - Takes "name" and "content" as required string arguments
     - Updates server state and notifies clients of resource changes

2. All of the Polygon API endpoints supported by the python client.

## Configuration

### Environment Variables

The following environment variables must be set for the server to function properly:

- `POLYGON_API_KEY`: Your Polygon.io API key

You can set this environment variable before running the server:

```bash
export POLYGON_API_KEY="your_polygon_api_key_here"
```

## Quickstart

### Install

#### Claude code

`claude mcp add polygon -e POLYGON_API_KEY=$POLY_API_KEY -- uv run /path/to/mcp_polygon/entrypoint.py`

## Development

### Building and Publishing

To prepare the package for distribution:

1. Sync dependencies and update lockfile:
```bash
uv sync
```

2. Build package distributions:
```bash
uv build
```

This will create source and wheel distributions in the `dist/` directory.

3. Publish to PyPI:
```bash
uv publish
```

Note: You'll need to set PyPI credentials via environment variables or command flags:
- Token: `--token` or `UV_PUBLISH_TOKEN`
- Or username/password: `--username`/`UV_PUBLISH_USERNAME` and `--password`/`UV_PUBLISH_PASSWORD`

### Debugging

Since MCP servers run over stdio, debugging can be challenging. For the best debugging
experience, we strongly recommend using the [MCP Inspector](https://github.com/modelcontextprotocol/inspector).


You can launch the MCP Inspector via [`npm`](https://docs.npmjs.com/downloading-and-installing-node-js-and-npm) with this command:

```bash
npx @modelcontextprotocol/inspector uv --directory /path/to/mcp_polygon run mcp_polygon
```


Upon launching, the Inspector will display a URL that you can access in your browser to begin debugging.
