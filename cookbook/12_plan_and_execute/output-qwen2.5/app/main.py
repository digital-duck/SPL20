
import fastapi
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uuid

app = FastAPI()

class TodoItem(BaseModel):
    id: str
    title: str
    description: str

class TodoList(BaseModel):
    items: list[TodoItem]

# Sample in-memory data store
todo_items = []
todo_lists = []

def get_id():
    return str(uuid.uuid4())

@app.post("/todos/")
async def create_todo(item: TodoItem):
    """Create a new todo item"""
    item.id = get_id()
    todo_items.append(item)
    return item

@app.get("/todos/")
async def read_todos():
    """Read all todo items"""
    return {"items": todo_items}

@app.get("/todos/{todo_id}")
async def read_todo(todo_id: str):
    """Read a specific todo item by id"""
    for item in todo_items:
        if item.id == todo_id:
            return item
    raise HTTPException(status_code=404, detail="Todo item not found")

@app.put("/todos/{todo_id}")
async def update_todo(todo_id: str, item: TodoItem):
    """Update a specific todo item by id"""
    for i, existing_item in enumerate(todo_items):
        if existing_item.id == todo_id:
            todo_items[i] = item
            return item
    raise HTTPException(status_code=404, detail="Todo item not found")

@app.delete("/todos/{todo_id}")
async def delete_todo(todo_id: str):
    """Delete a specific todo item by id"""
    for i, item in enumerate(todo_items):
        if item.id == todo_id:
            del todo_items[i]
            return {"message": "Todo item deleted"}
    raise HTTPException(status_code=404, detail="Todo item not found")

@app.get("/todo-lists/")
async def read_todo_lists():
    """Read all todo lists"""
    return {"lists": todo_lists}

@app.post("/todo-lists/")
async def create_todo_list(item: TodoList):
    """Create a new todo list"""
    item.id = get_id()
    todo_lists.append(item)
    return item

@app.get("/todo-lists/{todo_list_id}/items")
async def read_todo_items_in_list(todo_list_id: str):
    """Read all items in a specific todo list by id"""
    for i, list_item in enumerate(todo_lists):
        if list_item.id == todo_list_id:
            return {"items": [item.dict() for item in list_item.items]}
    raise HTTPException(status_code=404, detail="Todo list not found")

@app.put("/todo-lists/{todo_list_id}/items")
async def update_todo_items_in_list(todo_list_id: str, items: TodoList):
    """Update all items in a specific todo list by id"""
    for i, list_item in enumerate(todo_lists):
        if list_item.id == todo_list_id:
            list_item.items = items
            return {"message": "Items updated"}
    raise HTTPException(status_code=404, detail="Todo list not found")

@app.delete("/todo-lists/{todo_list_id}/items")
async def delete_todo_items_in_list(todo_list_id: str):
    """Delete all items in a specific todo list by id"""
    for i, list_item in enumerate(todo_lists):
        if list_item.id == todo_list_id:
            del list_item.items
            return {"message": "Items deleted"}
    raise HTTPException(status_code=404, detail="Todo list not found")
