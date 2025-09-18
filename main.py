# Filename: main.py
# Purpose: Main FastAPI application with corrected code order.

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import tracemalloc
import os

# Import your service functions
from app.services.nl_query_service import process_nl_query, check_service_health

# Debug print for the secret
print(f'>>> DEBUG: Reading ENABLE_MEMORY_TRACER secret. Value is: "{os.getenv("ENABLE_MEMORY_TRACER")}"')

# --- App Setup ---
# CRITICAL FIX: 'app' must be defined before it is used by the tracer.
app = FastAPI()

# --- Memory Tracer Start (Now Configurable) ---
if os.getenv("ENABLE_MEMORY_TRACER") == "true":
    tracemalloc.start()
    memory_snapshots = []

    @app.get("/api/debug/snapshot")
    async def take_memory_snapshot():
        """Takes a snapshot of the current memory allocation."""
        memory_snapshots.append(tracemalloc.take_snapshot())
        return {"status": "success", "snapshot_count": len(memory_snapshots)}

    @app.get("/api/debug/compare")
    async def compare_memory_snapshots():
        """Compares the last two memory snapshots to find potential leaks."""
        if len(memory_snapshots) < 2:
            return {"error": "Not enough snapshots to compare. Please take at least two."}
        
        snapshot1 = memory_snapshots[-2]
        snapshot2 = memory_snapshots[-1]
        top_stats = snapshot2.compare_to(snapshot1, 'lineno')
        
        results = [str(stat) for stat in top_stats[:10]]
        return {"top_10_memory_diff": results}
# --- Memory Tracer End ---

# Add CORS Middleware for local development
origins = ["http://localhost:5173"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount the '/assets' path
app.mount("/assets", StaticFiles(directory="console/dist/assets"), name="assets")

# Mount the templates directory
templates = Jinja2Templates(directory="console/dist")

class QueryRequest(BaseModel):
    nl_query: str
    page: int = 1

# --- API Endpoints ---
@app.post("/api/query")
async def api_query(request: QueryRequest):
    return process_nl_query(request.nl_query, request.page)

@app.get("/api/health")
async def api_health_all():
    return check_service_health()

@app.get("/api/health/{service_name}")
async def api_health_specific(service_name: str):
    return check_service_health(service_name=service_name)

# --- Frontend Serving ---
@app.get("/{full_path:path}", response_class=HTMLResponse)
async def serve_frontend(request: Request, full_path: str):
    return templates.TemplateResponse("index.html", {"request": request})

# -- end of file --
