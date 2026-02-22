"""
Minimal Task Tracking App - FastAPI + SQLite + Jinja
"""
import sqlite3
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from contextlib import contextmanager
from typing import Optional

app = FastAPI()
templates = Jinja2Templates(directory="app/templates")

DB_PATH = "tasks.db"

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

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    with get_db() as conn:
        lists = conn.execute("SELECT * FROM lists").fetchall()
        result = []
        for lst in lists:
            tasks = conn.execute(
                "SELECT * FROM tasks WHERE list_id = ?", (lst["id"],)
            ).fetchall()
            result.append({"list": lst, "tasks": tasks})
    return templates.TemplateResponse("index.html", {"request": request, "data": result})

@app.post("/list/create")
async def create_list(name: str = Form(...)):
    with get_db() as conn:
        conn.execute("INSERT INTO lists (name) VALUES (?)", (name,))
        conn.commit()
    return {"status": "ok"}

@app.post("/list/delete")
async def delete_list(list_id: int = Form(...)):
    with get_db() as conn:
        conn.execute("DELETE FROM tasks WHERE list_id = ?", (list_id,))
        conn.execute("DELETE FROM lists WHERE id = ?", (list_id,))
        conn.commit()
    return {"status": "ok"}

@app.post("/task/add")
async def add_task(list_id: int = Form(...), title: str = Form(...)):
    with get_db() as conn:
        conn.execute("INSERT INTO tasks (list_id, title) VALUES (?, ?)", (list_id, title))
        conn.commit()
    return {"status": "ok"}

@app.post("/task/toggle")
async def toggle_task(task_id: int = Form(...)):
    with get_db() as conn:
        task = conn.execute("SELECT done FROM tasks WHERE id = ?", (task_id,)).fetchone()
        new_done = 0 if task["done"] else 1
        conn.execute("UPDATE tasks SET done = ? WHERE id = ?", (new_done, task_id))
        conn.commit()
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    init_db()
    uvicorn.run(app, host="0.0.0.0", port=8000)
