#!/usr/bin/env python
"""
HTTP wrapper for polygon-mcp using FastMCP 2.3.2+ http_app() method.
This wrapper works without modifying the original polygon-mcp source code.

Usage with uvicorn:
    uvicorn http_wrapper:app --host 0.0.0.0 --port 8000
"""

import sys
import importlib

# Ensure the source is in the path
sys.path.insert(0, '/app/src')

def create_app():
    """
    Dynamically create the HTTP app from polygon-mcp's FastMCP instance.
    Works with both bundled (mcp.server.fastmcp) and standalone (fastmcp) versions.
    """
    try:
        # Import the server module to get the poly_mcp instance
        from mcp_polygon.server import poly_mcp
        
        # Check if http_app method is available (FastMCP 2.3.2+)
        if hasattr(poly_mcp, 'http_app'):
            print("✅ Using FastMCP http_app() method")
            return poly_mcp.http_app()
        else:
            # Fallback: Try to upgrade to standalone FastMCP if using bundled version
            try:
                # Check if we're using the bundled version
                if poly_mcp.__class__.__module__ == 'mcp.server.fastmcp':
                    print("⚠️  Detected bundled FastMCP, attempting to use standalone version...")
                    
                    # Try importing standalone FastMCP
                    from fastmcp import FastMCP
                    
                    # If standalone FastMCP has http_app, we need to recreate the instance
                    # This is a bit hacky but allows us to work without modifying source
                    if hasattr(FastMCP, 'http_app'):
                        print("✅ Standalone FastMCP with http_app() available")
                        # The poly_mcp instance is already created and has all the tools registered
                        # We can try to access its internal app if it exists
                        if hasattr(poly_mcp, '_app'):
                            return poly_mcp._app
                        else:
                            # As a last resort, create a new FastMCP instance
                            # Note: This won't have the tools registered, but it's better than failing
                            print("⚠️  Creating new FastMCP instance (tools may not be available)")
                            new_mcp = FastMCP("Polygon", dependencies=["polygon"])
                            return new_mcp.http_app()
                    else:
                        raise RuntimeError("Standalone FastMCP doesn't have http_app() method")
                else:
                    raise RuntimeError(f"FastMCP instance doesn't have http_app() method")
                    
            except ImportError as e:
                raise RuntimeError(f"FastMCP 2.3.2+ with http_app() support is required. Error: {e}")
                
    except Exception as e:
        print(f"❌ Error creating HTTP app: {e}")
        raise

# Create the app instance for uvicorn
app = create_app()

if __name__ == "__main__":
    # For testing - run with uvicorn
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)