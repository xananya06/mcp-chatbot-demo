FROM python:3.13-slim

# Install Git and clean up cache to keep the image small
RUN apt-get update && \
    apt-get install -y git && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* && \
    pip install --upgrade pip && \
    pip install poetry && \
    poetry self add poetry-plugin-export

COPY pyproject.toml poetry.lock README.md /app/

WORKDIR /app

# Set environment variables
ENV PYTHONPATH=/app \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN poetry export -f requirements.txt --without-hashes > requirements.txt && \
    pip install --no-cache-dir -r requirements.txt && \
    rm requirements.txt

# Copy project
COPY . .

# Run the application
CMD ["./run.sh"]