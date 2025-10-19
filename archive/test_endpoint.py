#!/usr/bin/env python3
from fastapi import FastAPI, Query
from typing import Optional, List
from pydantic import BaseModel

app = FastAPI()

class Item(BaseModel):
    id: int
    name: str

class ItemList(BaseModel):
    items: List[Item]
    total: int

@app.get("/items", response_model=ItemList)
async def get_items(
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=1000)
):
    return {
        "items": [],
        "total": 0
    }

if __name__ == "__main__":
    import uvicorn
    print("Test app OK")
    uvicorn.run(app, host="0.0.0.0", port=9000)
