from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime
from typing import Optional

from database import get_db, engine, Base
from models.todo import Todo  # registers Todo on shared Base

# Create tables on startup (skip if using Alembic migrations)
Base.metadata.create_all(bind=engine)

# --- Pydantic Schemas ---
PRIORITIES = {'low', 'medium', 'high'}

class TodoCreate(BaseModel):
    title: str
    completed: bool = False
    priority: str = 'medium'

class TodoUpdate(BaseModel):
    title: Optional[str] = None
    completed: Optional[bool] = None
    priority: Optional[str] = None

class TodoResponse(BaseModel):
    id: int
    title: str
    completed: bool
    priority: str
    created_at: datetime

    class Config:
        from_attributes = True

# --- App ---
app = FastAPI(title="Todo API", version="1.0.0")

# Allow all origins for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/", include_in_schema=False)
def root():
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/docs")

@app.post("/todos", response_model=TodoResponse, status_code=201)
def create_todo(payload: TodoCreate, db: Session = Depends(get_db)):
    """Create a new todo item."""
    if payload.priority not in PRIORITIES:
        raise HTTPException(status_code=422, detail=f"priority must be one of {PRIORITIES}")
    todo = Todo(title=payload.title, completed=payload.completed, priority=payload.priority)
    db.add(todo)
    db.commit()
    db.refresh(todo)
    return todo

@app.get("/todos", response_model=list[TodoResponse])
def list_todos(
    completed: Optional[bool] = None,
    db: Session = Depends(get_db),
):
    """List all todos, optionally filtered by completion status."""
    stmt = select(Todo)
    if completed is not None:
        stmt = stmt.where(Todo.completed == completed)  # type: ignore[arg-type]
    stmt = stmt.order_by(Todo.created_at.desc())  # type: ignore[arg-type]
    return db.execute(stmt).scalars().all()

@app.get("/todos/{todo_id}", response_model=TodoResponse)
def get_todo(todo_id: int, db: Session = Depends(get_db)):
    """Retrieve a single todo by ID."""
    todo = db.get(Todo, todo_id)
    if not todo:
        raise HTTPException(status_code=404, detail="Todo not found")
    return todo

@app.patch("/todos/{todo_id}", response_model=TodoResponse)
def update_todo(todo_id: int, payload: TodoUpdate, db: Session = Depends(get_db)):
    """Partially update a todo's title or completed status."""
    todo = db.get(Todo, todo_id)
    if not todo:
        raise HTTPException(status_code=404, detail="Todo not found")
    if payload.title is not None:
        todo.title = payload.title
    if payload.completed is not None:
        todo.completed = payload.completed
    if payload.priority is not None:
        if payload.priority not in PRIORITIES:
            raise HTTPException(status_code=422, detail=f"priority must be one of {PRIORITIES}")
        todo.priority = payload.priority
    db.commit()
    db.refresh(todo)
    return todo

@app.delete("/todos/{todo_id}", status_code=204)
def delete_todo(todo_id: int, db: Session = Depends(get_db)):
    """Delete a todo by ID."""
    todo = db.get(Todo, todo_id)
    if not todo:
        raise HTTPException(status_code=404, detail="Todo not found")
    db.delete(todo)
    db.commit()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
