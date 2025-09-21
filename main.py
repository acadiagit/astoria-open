# Filename: main.py
# Purpose: Main FastAPI application with singleton agent pattern.

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import os

# Import the agent creation function
from app.rag_components.agent_setup import create_maritime_agent
# Import the updated service functions
from app.services.nl_query_service import process_nl_query, check_service_health

# --- App Setup ---
app = FastAPI()

# --- Load Agent on Startup (Singleton Pattern) ---
@app.on_event("startup")
async def startup_event():
    """Create the agent executor only once when the app starts."""
    print("--- Loading Maritime Agent on startup... ---")
    # Store the agent in the application's state
    app.state.agent_executor = create_maritime_agent()
    print("--- Maritime Agent loaded successfully. ---")

# Add CORS Middleware
origins = ["http://localhost:5173"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files and templates
app.mount("/assets", StaticFiles(directory="console/dist/assets"), name="assets")
templates = Jinja2Templates(directory="console/dist")

class QueryRequest(BaseModel):
    nl_query: str
    page: int = 1

# --- API Endpoints ---
@app.post("/api/query")
async def api_query(request: QueryRequest):
    # Retrieve the pre-loaded agent from app.state
    agent = request.app.state.agent_executor
    # Pass the agent to the service function
    return process_nl_query(agent, request.nl_query, request.page)

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
