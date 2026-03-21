
import os
import uvicorn

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional

app = FastAPI()

class TodoItem(BaseModel):
    id: int
    title: str
    done: bool

# Sample in-memory data store (replace with a database in production)
todo_items = [
    {"id": 1, "title": "Buy milk", "done": False},
    {"id": 2, "title": "Walk the dog", "done": True},
]

@app.get("/todos/")
async def read_todos():
    return todo_items

@app.get("/todos/{todo_id}")
async def read_todo(todo_id: int):
    for item in todo_items:
        if item["id"] == todo_id:
            return item
    raise HTTPException(status_code=404, detail="Todo item not found")

@app.post("/todos/")
async def create_todo(todo_item: TodoItem):
    new_item = {
        "id": len(todo_items) + 1,
        "title": todo_item.title,
        "done": False,
    }
    todo_items.append(new_item)
    return new_item

@app.put("/todos/{todo_id}")
async def update_todo(todo_id: int, todo_item: TodoItem):
    for i, item in enumerate(todo_items):
        if item["id"] == todo_id:
            todo_items[i] = {
                "id": todo_id,
                "title": todo_item.title,
                "done": todo_item.done,
            }
            return todo_items[i]
    raise HTTPException(status_code=404, detail="Todo item not found")

@app.delete("/todos/{todo_id}")
async def delete_todo(todo_id: int):
    for i, item in enumerate(todo_items):
        if item["id"] == todo_id:
            del todo_items[i]
            return {"message": "Todo item deleted"}
    raise HTTPException(status_code=404, detail="Todo item not found")

if __name__ == "__main__":
    # Run the FastAPI app on port 8000
    uvicorn.run(app, host="0.0.0.0", port=8000)
