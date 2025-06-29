#!/bin/bash

set -e
set -o pipefail

if [ -e ./.env ]; then
  echo "Using .env file"
  source ./.env
fi

docker compose -f docker-compose-dev.yml up -d
docker compose down agent

export POSTGRES_SERVER=localhost
export AGENT_CONFIG_YAML="
        # FastAgent Configuration File
        # Default Model Configuration:
        #
        # Takes format:
        #   <provider>.<model_string>.<reasoning_effort?> (e.g. anthropic.claude-3-5-sonnet-20241022 or openai.o3-mini.low)
        # Accepts aliases for Anthropic Models: haiku, haiku3, sonnet, sonnet35, opus, opus3
        # and OpenAI Models: gpt-4o-mini, gpt-4o, o1, o1-mini, o3-mini
        #
        # If not specified, defaults to 'haiku'.
        # Can be overriden with a command line switch --model=<model>, or within the Agent constructor.

        default_model: haiku

        Logging and Console Configuration:
        logger:
          level: 'debug'
          type: 'console'
          progress_display: false
          show_chat: true
          show_tools: true
          otel:
            enabled: false
            console_debug: true

        # MCP Servers
        mcp:
          servers: # NOTE: Use underscores instead of hyphens for server names
            server_fetch:
                transport: 'sse'
                url: 'http://localhost:8901/sse'
                read_timeout_seconds: 65534
                read_transport_sse_timeout_seconds: 65534
            server_brave_search:
                transport: 'sse'
                url: 'http://localhost:8902/sse'
                read_timeout_seconds: 65534
                read_transport_sse_timeout_seconds: 65534
            server_sequential_thinking:
                transport: 'sse'
                url: 'http://localhost:8903/sse'
                read_timeout_seconds: 65534
                read_transport_sse_timeout_seconds: 65534
            server_memory:
                transport: 'sse'
                url: 'http://localhost:8904/sse'
                read_timeout_seconds: 65534
                read_transport_sse_timeout_seconds: 65534"

cd ../../src/agent
./run.sh