# FastAPI Chat Backend

A production-ready FastAPI backend that supports a chat API.

## Features

- RESTful API with FastAPI
- PostgreSQL database with SQLAlchemy ORM
- Authentication with JWT tokens (placeholder)
- Basic test infrastructure with pytest

## Requirements

- Python 3.9+

## API Endpoints

- **GET /health**: Health check endpoint
- **POST /api/v1/chat**: Send a message to the chat API
- **GET /api/v1/conversations**: Get all conversations for the current user
- **GET /api/v1/conversations/{conversation_id}/messages**: Get all messages for a specific conversation

## Running Tests

```bash
pytest
```

## Development

### Database Migrations

This project uses Alembic for database migrations.

To create a new migration:
```bash
alembic revision --autogenerate -m "Description of the change"
```

To apply migrations:
```bash
alembic upgrade head
```

## Project Structure

```
backend/
├── app/                 # Application package
│   ├── api/             # API endpoints
│   ├── core/            # Core functionality (config, security)
│   ├── db/              # Database models and session
│   ├── models/          # SQLAlchemy models
│   ├── schemas/         # Pydantic schemas for validation
│   └── services/        # Business logic
├── tests/               # Tests package
├── .env                 # Environment variables
├── Dockerfile           # Docker configuration
└── requirements.txt     # Python dependencies
```
