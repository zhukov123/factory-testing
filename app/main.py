"""
Minimal Task Tracking App - FastAPI + SQLite + Jinja
With input validation, error handling, and API key authentication.
"""
import sqlite3
from fastapi import FastAPI, Request, Form, HTTPException, Header, status
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from contextlib import contextmanager
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator

app = FastAPI()
templates = Jinja2Templates(directory="app/templates")

DB_PATH = "tasks.db"
API_KEY = "task-app-secret-key"  # In production, use environment variable

# Pydantic models for validation
class ListCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)

class ListDelete(BaseModel):
    list_id: int = Field(..., gt=0)

class TaskAdd(BaseModel):
    list_id: int = Field(..., gt=0)
    title: str = Field(..., min_length=1, max_length=500)

class TaskToggle(BaseModel):
    task_id: int = Field(..., gt=0)

class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None

@contextmanager
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

def init_db():
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS lists (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                list_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                done INTEGER DEFAULT 0,
                FOREIGN KEY (list_id) REFERENCES lists (id)
            )
        """)
        conn.commit()

def verify_api_key(x_api_key: str = Header(...)) -> str:
    """Verify API key for protected endpoints."""
    if x_api_key != API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )
    return x_api_key

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Home page - displays all lists and tasks."""
    try:
        with get_db() as conn:
            lists = conn.execute("SELECT * FROM lists").fetchall()
            result = []
            for lst in lists:
                tasks = conn.execute(
                    "SELECT * FROM tasks WHERE list_id = ?", (lst["id"],)
                ).fetchall()
                result.append({"list": lst, "tasks": tasks})
        return templates.TemplateResponse("index.html", {"request": request, "data": result})
    except sqlite3.Error as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )

@app.post("/list/create")
async def create_list(
    name: str = Form(..., min_length=1, max_length=100),
    x_api_key: str = Header(...)
):
    """Create a new list. Requires API key authentication."""
    verify_api_key(x_api_key)
    
    if not name or not name.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="List name cannot be empty"
        )
    
    try:
        with get_db() as conn:
            cursor = conn.execute("INSERT INTO lists (name) VALUES (?)", (name.strip(),))
            conn.commit()
            list_id = cursor.lastrowid
        return {"status": "ok", "list_id": list_id}
    except sqlite3.IntegrityError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Database integrity error: {str(e)}"
        )
    except sqlite3.Error as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )

@app.post("/list/delete")
async def delete_list(
    list_id: int = Form(..., gt=0),
    x_api_key: str = Header(...)
):
    """Delete a list and all its tasks. Requires API key authentication."""
    verify_api_key(x_api_key)
    
    try:
        with get_db() as conn:
            # Verify list exists
            lst = conn.execute("SELECT id FROM lists WHERE id = ?", (list_id,)).fetchone()
            if not lst:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"List with id {list_id} not found"
                )
            
            conn.execute("DELETE FROM tasks WHERE list_id = ?", (list_id,))
            conn.execute("DELETE FROM lists WHERE id = ?", (list_id,))
            conn.commit()
        return {"status": "ok", "message": f"List {list_id} deleted"}
    except sqlite3.Error as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )

@app.post("/task/add")
async def add_task(
    list_id: int = Form(..., gt=0),
    title: str = Form(..., min_length=1, max_length=500),
    x_api_key: str = Header(...)
):
    """Add a task to a list. Requires API key authentication."""
    verify_api_key(x_api_key)
    
    if not title or not title.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Task title cannot be empty"
        )
    
    try:
        with get_db() as conn:
            # Verify list exists
            lst = conn.execute("SELECT id FROM lists WHERE id = ?", (list_id,)).fetchone()
            if not lst:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"List with id {list_id} not found"
                )
            
            cursor = conn.execute(
                "INSERT INTO tasks (list_id, title) VALUES (?, ?)", 
                (list_id, title.strip())
            )
            conn.commit()
            task_id = cursor.lastrowid
        return {"status": "ok", "task_id": task_id}
    except sqlite3.IntegrityError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Database integrity error: {str(e)}"
        )
    except sqlite3.Error as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )

@app.post("/task/toggle")
async def toggle_task(
    task_id: int = Form(..., gt=0),
    x_api_key: str = Header(...)
):
    """Toggle task done status. Requires API key authentication."""
    verify_api_key(x_api_key)
    
    try:
        with get_db() as conn:
            task = conn.execute("SELECT id, done FROM tasks WHERE id = ?", (task_id,)).fetchone()
            if not task:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Task with id {task_id} not found"
                )
            
            new_done = 0 if task["done"] else 1
            conn.execute("UPDATE tasks SET done = ? WHERE id = ?", (new_done, task_id))
            conn.commit()
        return {"status": "ok", "task_id": task_id, "done": bool(new_done)}
    except sqlite3.Error as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )

# JSON API endpoints (alternative to form-based)
@app.post("/api/lists")
async def create_list_json(
    list_data: ListCreate,
    x_api_key: str = Header(...)
):
    """Create a new list (JSON API). Requires API key authentication."""
    verify_api_key(x_api_key)
    
    try:
        with get_db() as conn:
            cursor = conn.execute("INSERT INTO lists (name) VALUES (?)", (list_data.name.strip(),))
            conn.commit()
            list_id = cursor.lastrowid
        return {"status": "ok", "list_id": list_id, "name": list_data.name}
    except sqlite3.Error as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )

@app.get("/api/lists")
async def get_lists():
    """Get all lists (JSON API). Public endpoint."""
    try:
        with get_db() as conn:
            lists = conn.execute("SELECT * FROM lists").fetchall()
            return [{"id": lst["id"], "name": lst["name"]} for lst in lists]
    except sqlite3.Error as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )

@app.delete("/api/lists/{list_id}")
async def delete_list_json(
    list_id: int,
    x_api_key: str = Header(...)
):
    """Delete a list (JSON API). Requires API key authentication."""
    verify_api_key(x_api_key)
    
    try:
        with get_db() as conn:
            lst = conn.execute("SELECT id FROM lists WHERE id = ?", (list_id,)).fetchone()
            if not lst:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"List with id {list_id} not found"
                )
            
            conn.execute("DELETE FROM tasks WHERE list_id = ?", (list_id,))
            conn.execute("DELETE FROM lists WHERE id = ?", (list_id,))
            conn.commit()
        return {"status": "ok", "message": f"List {list_id} deleted"}
    except sqlite3.Error as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )

@app.post("/api/tasks")
async def add_task_json(
    task_data: TaskAdd,
    x_api_key: str = Header(...)
):
    """Add a task (JSON API). Requires API key authentication."""
    verify_api_key(x_api_key)
    
    try:
        with get_db() as conn:
            lst = conn.execute("SELECT id FROM lists WHERE id = ?", (task_data.list_id,)).fetchone()
            if not lst:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"List with id {task_data.list_id} not found"
                )
            
            cursor = conn.execute(
                "INSERT INTO tasks (list_id, title) VALUES (?, ?)", 
                (task_data.list_id, task_data.title.strip())
            )
            conn.commit()
            task_id = cursor.lastrowid
        return {"status": "ok", "task_id": task_id, "title": task_data.title}
    except sqlite3.Error as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )

@app.get("/api/lists/{list_id}/tasks")
async def get_tasks(list_id: int):
    """Get tasks for a list (JSON API). Public endpoint."""
    try:
        with get_db() as conn:
            lst = conn.execute("SELECT id FROM lists WHERE id = ?", (list_id,)).fetchone()
            if not lst:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"List with id {list_id} not found"
                )
            
            tasks = conn.execute("SELECT * FROM tasks WHERE list_id = ?", (list_id,)).fetchall()
            return [{"id": t["id"], "list_id": t["list_id"], "title": t["title"], "done": bool(t["done"])} for t in tasks]
    except sqlite3.Error as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )

@app.patch("/api/tasks/{task_id}/toggle")
async def toggle_task_json(
    task_id: int,
    x_api_key: str = Header(...)
):
    """Toggle task status (JSON API). Requires API key authentication."""
    verify_api_key(x_api_key)
    
    try:
        with get_db() as conn:
            task = conn.execute("SELECT id, done FROM tasks WHERE id = ?", (task_id,)).fetchone()
            if not task:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Task with id {task_id} not found"
                )
            
            new_done = 0 if task["done"] else 1
            conn.execute("UPDATE tasks SET done = ? WHERE id = ?", (new_done, task_id))
            conn.commit()
        return {"status": "ok", "task_id": task_id, "done": bool(new_done)}
    except sqlite3.Error as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn
    init_db()
    uvicorn.run(app, host="0.0.0.0", port=8000)
