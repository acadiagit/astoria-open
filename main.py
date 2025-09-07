# Filename: main.py
# Purpose: Main FastAPI application with CORS enabled for development.

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import Optional

# --- NEW: Import the CORSMiddleware ---
from fastapi.middleware.cors import CORSMiddleware

# Import your service functions
from app.services.nl_query_service import process_nl_query, check_service_health

# --- App Setup ---
app = FastAPI()

# --- NEW: Add CORS Middleware to allow requests from your frontend dev server ---
origins = [
    "http://localhost:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"], # Allows all methods (GET, POST, etc.)
    allow_headers=["*"], # Allows all headers
)


app.mount("/static", StaticFiles(directory="console/dist/assets"), name="static")
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
    """Returns the status of all external services."""
    return check_service_health()

@app.get("/api/health/{service_name}")
async def api_health_specific(service_name: str):
    """Returns the status of a specific external service."""
    return check_service_health(service_name=service_name)

# --- Frontend Serving ---
@app.get("/{full_path:path}", response_class=HTMLResponse)
async def serve_frontend(request: Request, full_path: str):
    return templates.TemplateResponse("index.html", {"request": request})

# -- end of file --
