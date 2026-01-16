# [main.py]
# Purpose: Main FastAPI application for the Astoria Open RAG platform.
# Implements the full SQL + RAG pipeline and serves the React frontend.
# --- FINAL PRODUCTION VERSION (UI & Logic Fix): 11/18/2025 ---

import sys
import os
import logging
import tracemalloc
import threading
import time
import psutil
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

# --- RAG IMPORTS ---
from langchain_groq import ChatGroq
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
# --- END RAG IMPORTS ---

# Import project functions
from app.rag_components.agent_setup import create_maritime_agent
from nl2sql.nl2sql_service import NL2SQLService
from utils.db_utils import get_db_connection, get_vector_store

# --- Narrative Synthesis Prompt (FIXED: Re-inserted missing global variable) ---
NARRATIVE_SYNTHESIS_TEMPLATE = """
You are an expert maritime historian. Your task is to synthesize information from two sources:
1.  A structured data table (SQL Results).
2.  Unstructured text context (Vector Search Results).

Combine these sources to answer the user's question in a single, cohesive, narrative answer.
If the SQL Results are empty, rely only on the Vector Search Results, and vice-versa.
If both are empty, just say "I could not find any information about that."

USER QUESTION: {question}

SQL RESULTS:
{sql_data}

VECTOR SEARCH RESULTS:
{vector_data}

YOUR SYNTHESIZED NARRATIVE:
"""
# --- END Narrative Synthesis Prompt ---


# --- Periodic Memory Logger Start ---
def start_memory_logger():
    """Starts a background thread to log memory usage every hour."""
    
    def log_memory():
        process = psutil.Process(os.getpid())
        # RSS: Resident Set Size - the non-swapped physical memory a process has used.
        memory_mb = process.memory_info().rss / (1024 * 1024)
        print(f"🧠 MEMORY LOG: Current usage: {memory_mb:.2f} MB")

    def memory_log_worker():
        while True:
            log_memory()
            time.sleep(3600) # Sleep for 1 hour (3600 seconds)

    thread = threading.Thread(target=memory_log_worker, daemon=True)
    thread.start()
    print("✅ Memory logger background thread started.")

# Start the logger when the application boots
start_memory_logger()
# --- Periodic Memory Logger End ---


# --- Force Detailed Logging ---
logging.basicConfig(stream=sys.stdout, level=logging.INFO)

# --- App Setup ---
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


# --- CORS Middleware (FINAL FIX) ---
# This is the final working CORS configuration.
origins = [
    "http://localhost:5173",  # For local Vite development
    "http://localhost:7860",  # For production (when FastAPI serves the built files)
    "http://127.0.0.1:7860",  # For robust local host connections
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Load All Services and Connect Them on Startup ---
@app.on_event("startup")
async def startup_event():
    """Create all service instances and connect them when the app starts."""
    print("--- Connecting to database... ---")
    app.state.db_connection = get_db_connection()
    print("--- Database connection successful. ---")
    
    agent_factory = create_maritime_agent
    
    print("--- Loading NL2SQL Service with Agent Bridge... ---")
    app.state.nl2sql_service = NL2SQLService(
        db_connection=app.state.db_connection,
        langchain_agent_factory=agent_factory
    )
    
    # --- Load RAG Components ---
    print("--- Loading Embedding Model (SentenceTransformer)... ---")
    app.state.embedding_model = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        model_kwargs={'device': 'cpu'},
        encode_kwargs={'normalize_embeddings': True}
    )
    
    print("--- Loading Vector Store (Supabase)... ---")
    app.state.vector_store = get_vector_store(app.state.embedding_model)
    
    print("--- Loading Narrative Synthesizer (Groq LLM)... ---")
    app.state.groq_llm = ChatGroq(
        temperature=0, 
        groq_api_key=os.getenv("GROQ_API_KEY"), 
        model_name="llama-3.1-8b-instant" # Fast and capable model
    )
    print("--- Services loaded successfully. ---")
    # --- END RAG COMPONENTS ---


@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources when the app shuts down."""
    if hasattr(app.state, 'db_connection') and app.state.db_connection:
        app.state.db_connection.close()
        print("--- Database connection closed. ---")

# --- Pydantic Model for API Request ---
class QueryRequest(BaseModel):
    nl_query: str
    page: int = 1


# --- API Endpoints ---

@app.get("/api/health")
async def api_health_all():
    """FIXED: Basic internal health check for the core services."""
    health_status = {
        "status": "ok",
        "db_connection": hasattr(app.state, 'db_connection') and app.state.db_connection is not None,
        "nl2sql_service": hasattr(app.state, 'nl2sql_service') and app.state.nl2sql_service is not None,
        "vector_store": hasattr(app.state, 'vector_store') and app.state.vector_store is not None,
        "groq_llm": hasattr(app.state, 'groq_llm') and app.state.groq_llm is not None,
    }
    # Determine overall status
    overall = all(health_status.values())
    health_status["status"] = "operational" if overall else "degraded"
    return health_status


@app.post("/api/query")
async def api_query(query_data: QueryRequest, request: Request):
    
    nl_query = query_data.nl_query
    print(f"\n--- Received Query: {nl_query} ---")

    # Get all singleton services from the app state
    nl_service = request.app.state.nl2sql_service
    vector_store = request.app.state.vector_store
    groq_llm = request.app.state.groq_llm
    
    # --- STEP 1: Get SQL Data ---
    print("Step 1: Processing NL-to-SQL...")
    sql_response = nl_service.process_query(nl_query)
    
    # --- STEP 2: Get Vector Data ---
    print("Step 2: Processing Vector Search...")
    try:
        # Find the top 3 most similar documents
        vector_docs = vector_store.similarity_search(nl_query, k=3)
        # Format for the prompt
        vector_data = "\n---\n".join([doc.page_content for doc in vector_docs])
    except Exception as e:
        print(f"Vector search failed: {e}")
        vector_data = "No vector data found."

    # --- STEP 3: Synthesize Narrative (The Final Logic Check) ---
    print("Step 3: Synthesizing final narrative with Groq...")

    # FIX: If the LLM Agent was used, its final human-readable answer is the response.
    if sql_response.processing_method == "llm_langchain":
        # Agent has already synthesized the answer text. Use it directly and skip Groq.
        final_narrative = sql_response.nl_response
        sql_data_for_prompt = final_narrative # For display in the final output JSON
        print("Agent provided final narrative, skipping Groq synthesis.")

    else:
        # This path is for the Simple Query Flow (always use Groq to synthesize).
        sql_data_for_prompt = sql_response.results if hasattr(sql_response, "results") and sql_response.results else "No SQL data found."

        prompt = ChatPromptTemplate.from_template(NARRATIVE_SYNTHESIS_TEMPLATE)
        
        synthesis_chain = (
            prompt |
            groq_llm |
            StrOutputParser()
        )
        
        final_narrative = synthesis_chain.invoke({
            "question": nl_query,
            "sql_data": sql_data_for_prompt,
            "vector_data": vector_data
        })
    
    print(f"Final Narrative: {final_narrative}")
    
    # --- STEP 4: Return Unified Response ---
    return {
        "success": True,
        "nl_query": nl_query,
        "nl_response": final_narrative, # The NEW synthesized answer (from Agent or Groq)
        "sql_query": sql_response.sql_query if hasattr(sql_response, "sql_query") else None,
        "sql_results": sql_response.results if hasattr(sql_response, "results") else None,
        "vector_context": vector_data,
        "processing_method": sql_response.processing_method if hasattr(sql_response, "processing_method") else "unknown",
        "execution_time": sql_response.execution_time if hasattr(sql_response, "execution_time") else 0.0
    }

# --- Frontend Static File Serving ---
# This mounts the 'dist' folder from your React build 
# to serve static files (like javascript, css)
app.mount("/assets", StaticFiles(directory="console/dist/assets"), name="assets")

# This serves the main index.html file for your React App
@app.get("/", response_class=FileResponse)
async def read_index():
    return "console/dist/index.html"

# This catches any other path and sends it to index.html
# This is required for React Router to work correctly
@app.exception_handler(404)
async def not_found_handler(request: Request, exc: Exception):
    return FileResponse("console/dist/index.html")

# -- end of file --
