FROM python:3.11-slim

# Install Git and clean up cache to keep the image small
RUN apt-get update && \
    apt-get install -y git && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* && \
    pip install --upgrade pip

# Copy files for context
COPY pyproject.toml README.md /app/
WORKDIR /app

# Set environment variables
ENV PYTHONPATH=/app \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Install dependencies directly with pip (bypasses poetry issues)
RUN pip install --no-cache-dir \
    alembic>=1.12.0 \
    bcrypt==3.2.2 \
    descope>=0.1.0 \
    fastapi>=0.103.1 \
    httpx>=0.25.0 \
    "opentelemetry-api>=1.31.1,<2.0.0" \
    openinference-instrumentation-mcp \
    opentelemetry-instrumentation-fastapi \
    opentelemetry-instrumentation-httpx \
    opentelemetry-instrumentation-threading \
    passlib>=1.7.4 \
    psycopg2-binary>=2.9.6 \
    pydantic>=2.4.2 \
    pydantic-settings>=2.0.3 \
    pytest>=7.4.2 \
    python-dotenv>=1.0.0 \
    "python-jose[cryptography]>=3.3.0" \
    python-multipart>=0.0.6 \
    sqlalchemy>=2.0.21 \
    uvicorn>=0.23.2 \
    "opentelemetry-sdk>=1.34.0,<2.0.0" \
    "opentelemetry-exporter-otlp>=1.34.0,<2.0.0" \
    aiohttp>=3.9.0 \
    beautifulsoup4>=4.12.0 \
    lxml>=4.9.0 \
    requests>=2.31.0

# Install fast-agent separately (since it's from git)
RUN pip install --no-cache-dir git+https://github.com/acuvity/fast-agent.git

# Copy project
COPY . .

# Run the application
CMD ["./run.sh"]