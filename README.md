# Chatbot example with agentic workflows

## Overview

This an example chatbot with agentic workflows.

<img width="1499" alt="mcp-demo-ui" src="https://github.com/user-attachments/assets/13303412-8f33-4785-a796-e7efdf1d753e" />

## Architecture 

In this demo, we will have the following components:

- A **Web Interface**, which presents a chat to the user. This is a simple ReactJS application making calls to an Agent
- An **Agent** uses Anthropic (optionnally, can use other LLMs as by supported by [Fast-agent](https://github.com/evalstate/fast-agent))
- A **Database** uses a postgres database to store and retrieve chat histories and conversations
- Some **[Secure MCP servers](https://mcp.acuvity.ai)** which provide additional capabilities to the **Agent**

> [!TIP]
> Add more Secure MCP Servers as needed to make your Chatbot more powerful!

<img width="819" alt="mcp-demo-architecture" src="https://github.com/user-attachments/assets/2be5c986-afd5-444c-932b-49a7cea26b09" />


### Framework used:

- [Fast-agent](https://github.com/evalstate/fast-agent) which supports the maximum features with regards to MCP.
- [Minibridge](https://github.com/acuvity/minibridge) makes it secure and production ready in the [secure MCP servers](https://mcp.acuvity.ai).
- [Descope](https://www.descope.com/) optionnally adds authentication and authorization support.

### Enterprise Ready MCP servers used:

- mcp-server-fetch [Dockerfile](https://github.com/acuvity/mcp-servers-registry/tree/main/mcp-server-fetch) [Container](https://hub.docker.com/r/acuvity/mcp-server-fetch)
- mcp-server-brave-search [Dockerfile](https://github.com/acuvity/mcp-servers-registry/tree/main/mcp-server-brave-search) [Container](https://hub.docker.com/r/acuvity/mcp-server-brave-search)
- mcp-server-github [Dockerfile](https://github.com/acuvity/mcp-servers-registry/tree/main/mcp-server-github) [Container](https://hub.docker.com/r/acuvity/mcp-server-github)
- mcp-server-sequential-thinking [Dockerfile](https://github.com/acuvity/mcp-servers-registry/tree/main/mcp-server-sequential-thinking) [Container](https://hub.docker.com/r/acuvity/mcp-server-sequential-thinking)
- mcp-server-memory [Dockerfile](https://github.com/acuvity/mcp-servers-registry/tree/main/mcp-server-memory) [Container](https://hub.docker.com/r/acuvity/mcp-server-memory)
- mcp-server-microsoft [Dockerfile](https://github.com/acuvity/mcp-servers-registry/tree/main/mcp-server-microsoft) [Container](https://hub.docker.com/r/acuvity/mcp-server-microsoft)

## Installation and Setup

### Getting started

- Clone the repository:

  ```bash
  git clone <repository-url>
  ```

### Deploying this on K8s

Follow the instructions [here](./deploy/k8s/README.md)

### Trying out the application with Docker Compose

Follow the instructions [here](./deploy/compose/README.md#trying-out-the-application-with-docker)

### Developing ui and agent (using Docker compose)

Follow the instructions [here](./deploy/compose/README.md#developing-ui-and-agent)

### Support for TLS

> [!TIP]
> For ease of use, we are using [tg](https://github.com/acuvity/tg) which is a simple
> TLS generator CLI: `tg cert --name server --ip 127.0.0.1 --dns localhost`

> [!WARNING]
> The certificates provided are only for ease of use and MUST not be used in production.

All certificates for MCP servers already exist in certs folder. You can update the `certs/init-certs.sh`

## API Endpoints

- **GET /health**: Health check endpoint
- **POST /api/v1/chat**: Send a message to the chat API
- **GET /api/v1/conversations**: Get all conversations for the current user
- **GET /api/v1/conversations/{conversation_id}/messages**: Get all messages for a specific conversation

## Running Tests

```bash
pytest
```
