FROM python:3.13-slim

WORKDIR /app

# Install uv for dependency management
RUN pip install uv

# Copy the entire polygon-mcp project
COPY . .

# Install dependencies from polygon-mcp
RUN uv pip install --system -e .

# Install FastMCP 2.3.2+ and uvicorn for HTTP support
RUN uv pip install --system "fastmcp>=2.3.2" "uvicorn[standard]"

# Set Python path to include the source directory
ENV PYTHONPATH=/app/src:$PYTHONPATH

# Use uvicorn to run our HTTP wrapper
CMD ["uvicorn", "http_wrapper:app", "--host", "0.0.0.0", "--port", "8000"]