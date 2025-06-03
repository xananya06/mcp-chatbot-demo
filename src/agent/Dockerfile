FROM python:3.13-slim

# Install Git and clean up cache to keep the image small
RUN apt-get update && \
    apt-get install -y git && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Set environment variables
ENV PYTHONPATH=/app \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Copy project
COPY . .

# Install dependencies
RUN pip install --no-cache-dir .

# Run the application
CMD ["./run.sh"]