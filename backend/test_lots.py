#!/usr/bin/env python3
"""Test script to isolate lots endpoint issue"""
import sys
from fastapi import FastAPI

# Create app
app = FastAPI()

# Try to import and include lots router
try:
    from app.api.v1.endpoints import lots
    print("✓ Successfully imported lots module")

    app.include_router(lots.router, prefix="/lots")
    print("✓ Successfully included lots router")

    print("\nAttempting to start server...")
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9000)

except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
