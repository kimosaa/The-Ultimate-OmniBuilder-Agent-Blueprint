# REST API Example

This example demonstrates OmniBuilder building a complete REST API.

## Goal

Build a FastAPI REST API with:
- User CRUD endpoints
- SQLite database
- Pydantic models
- Basic authentication

## Running with OmniBuilder

```bash
cd examples/rest_api

# Run the build
omnibuilder run "Create a FastAPI REST API with user CRUD, SQLite database, and basic auth"
```

## What OmniBuilder Should Create

1. `main.py` - FastAPI application
2. `models.py` - Pydantic models
3. `database.py` - SQLite database setup
4. `auth.py` - Authentication logic
5. `requirements.txt` - Dependencies
6. `README.md` - API documentation

## Testing the API

```bash
# Install dependencies
pip install -r requirements.txt

# Run the API
uvicorn main:app --reload

# Test endpoints
curl http://localhost:8000/docs
```

## Expected Endpoints

- `GET /users` - List all users
- `POST /users` - Create user
- `GET /users/{id}` - Get user by ID
- `PUT /users/{id}` - Update user
- `DELETE /users/{id}` - Delete user
- `POST /auth/login` - Login endpoint
