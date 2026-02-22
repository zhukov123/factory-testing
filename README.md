# Task Tracking App

A minimal task tracking web application built with FastAPI and SQLite.

## Features

- Create, view, and delete task lists
- Add and toggle tasks within lists
- Input validation for all endpoints
- API key authentication for modifying operations
- HTML web interface + JSON REST API

## Quick Start

### Installation

```bash
pip install -r requirements.txt
```

### Running the App

```bash
cd app
python main.py
```

The app will be available at `http://localhost:8000`

### Running Tests

```bash
pytest tests/unit/test_task_app.py -v
```

## API Endpoints

### Authentication

All modifying endpoints (POST, PUT, DELETE) require an API key passed in the `X-API-Key` header.

**Default API Key:** `task-app-secret-key`

In production, set the `API_KEY` environment variable.

---

### Lists

#### Get All Lists
```
GET /api/lists
```

**Response:**
```json
[
  {"id": 1, "name": "My Tasks"},
  {"id": 2, "name": "Shopping"}
]
```

#### Create List
```
POST /api/lists
Headers: X-API-Key: <your-api-key>
Body: {"name": "List Name"}
```

**Response:**
```json
{"status": "ok", "list_id": 1, "name": "List Name"}
```

#### Delete List
```
DELETE /api/lists/{list_id}
Headers: X-API-Key: <your-api-key>
```

**Response:**
```json
{"status": "ok", "message": "List 1 deleted"}
```

---

### Tasks

#### Get Tasks for List
```
GET /api/lists/{list_id}/tasks
```

**Response:**
```json
[
  {"id": 1, "list_id": 1, "title": "Buy milk", "done": false},
  {"id": 2, "list_id": 1, "title": "Call mom", "done": true}
]
```

#### Add Task
```
POST /api/tasks
Headers: X-API-Key: <your-api-key>
Body: {"list_id": 1, "title": "Task title"}
```

**Response:**
```json
{"status": "ok", "task_id": 3, "title": "Task title"}
```

#### Toggle Task Status
```
PATCH /api/tasks/{task_id}/toggle
Headers: X-API-Key: <your-api-key>
```

**Response:**
```json
{"status": "ok", "task_id": 3, "done": true}
```

---

## Web Interface

The app also provides an HTML interface at the root URL (`/`):

- View all lists and tasks
- Create new lists
- Delete lists
- Add tasks to lists
- Toggle task completion

---

## Form Endpoints (Alternative)

The app also supports form-based POST requests:

| Endpoint | Form Fields | Auth Required |
|----------|-------------|---------------|
| POST /list/create | `name` | Yes (X-API-Key header) |
| POST /list/delete | `list_id` | Yes |
| POST /task/add | `list_id`, `title` | Yes |
| POST /task/toggle | `task_id` | Yes |

---

## Validation Rules

- **List name:** 1-100 characters, cannot be empty or whitespace-only
- **Task title:** 1-500 characters, cannot be empty or whitespace-only
- **List/Task ID:** Must be a positive integer

---

## Error Responses

| Status Code | Description |
|-------------|-------------|
| 400 | Bad request (validation failed) |
| 401 | Unauthorized (invalid/missing API key) |
| 404 | Not found (resource doesn't exist) |
| 422 | Validation error (Pydantic validation) |
| 500 | Internal server error |

Example error response:
```json
{
  "detail": "List with id 999 not found"
}
```

---

## License

MIT
