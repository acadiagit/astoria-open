# Filename: main.py
# Purpose: Final main FastAPI application with a robust path fix.

import sys
import os

# --- ADD THIS BLOCK TO FIX THE IMPORT PATH ---
# This explicitly adds the project's root directory ('/app' in the container)
# to the list of places Python looks for modules.
# This is a robust way to ensure all local modules are found.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))
# --- END PATH FIX BLOCK ---

import logging
import tracemalloc
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

# Import project functions
from app.rag_components.agent_setup import create_maritime_agent
from app.services.nl_query_service import process_nl_query, check_service_health

# --- Force Detailed Logging ---
logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

# --- App Setup ---
app = FastAPI()

# --- Load Agent on Startup (Singleton Pattern) ---
@app.on_event("startup")
async def startup_event():
    """Create the agent executor only once when the app starts."""
    print("--- Loading Maritime Agent on startup... ---")
    app.state.agent_executor = create_maritime_agent()
    print("--- Maritime Agent loaded successfully. ---")

# (The rest of the file remains the same)
# ...
# --- Memory Tracer (Configurable) ---
if os.getenv("ENABLE_MEMORY_TRACER") == "true":
    tracemalloc.start()
    memory_snapshots = []

    @app.get("/api/debug/snapshot")
    async def take_memory_snapshot():
        memory_snapshots.append(tracemalloc.take_snapshot())
        return {"status": "success", "snapshot_count": len(memory_snapshots)}

    @app.get("/api/debug/compare")
    async def compare_memory_snapshots():
        if len(memory_snapshots) < 2:
            return {"error": "Not enough snapshots to compare."}
        
        snapshot1 = memory_snapshots[-2]
        snapshot2 = memory_snapshots[-1]
        top_stats = snapshot2.compare_to(snapshot1, 'lineno')
        
        results = [str(stat) for stat in top_stats[:10]]
        return {"top_10_memory_diff": results}

# --- Standard Middleware and Routing ---
origins = ["http://localhost:5173"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/assets", StaticFiles(directory="console/dist/assets"), name="assets")
templates = Jinja2Templates(directory="console/dist")

class QueryRequest(BaseModel):
    nl_query: str
    page: int = 1

@app.post("/api/query")
async def api_query(query_data: QueryRequest, request: Request):
    agent = request.app.state.agent_executor
    return process_nl_query(agent, query_data.nl_query, query_data.page)

@app.get("/api/health")
async def api_health_all():
    return check_service_health()

@app.get("/api/health/{service_name}")
async def api_health_specific(service_name: str):
    return check_service_health(service_name=service_name)

@app.get("/{full_path:path}", response_class=HTMLResponse)
async def serve_frontend(request: Request, full_path: str):
    return templates.TemplateResponse("index.html", {"request": request})

# -- end of file --
