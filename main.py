# [main.py]
# Purpose: Main FastAPI application for the Astoria Open RAG platform.
# Implements the full SQL + RAG pipeline and serves the React frontend.

import sys
import os
import logging
import tracemalloc
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

# --- ADD THIS BLOCK TO FIX THE IMPORT PATH ---
# Ensures 'utils' and 'nl2sql' can be found
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))
# --- END PATH FIX BLOCK ---

# --- RAG IMPORTS ---
from langchain_groq import ChatGroq
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
# --- END RAG IMPORTS ---

# Import project functions
from app.rag_components.agent_setup import create_maritime_agent
from nl2sql.nl2sql_service import NL2SQLService
from utils.db_utils import get_db_connection, get_vector_store

# --- Force Detailed Logging ---
logging.basicConfig(stream=sys.stdout, level=logging.INFO)

# --- App Setup ---
app = FastAPI()

# --- CORS Middleware ---
# Allows your React frontend (on a different port during dev) to talk to this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
)

# --- Narrative Synthesis Prompt ---
# This is the prompt for your "Narrative Synthesizer" (Groq) [cite: 34]
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
    
    # --- NEW: Load RAG Components ---
    print("--- Loading Embedding Model (SentenceTransformer)... ---")
    # This is the Embeddings Model from your architecture diagram [cite: 33]
    app.state.embedding_model = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        model_kwargs={'device': 'cpu'},
        encode_kwargs={'normalize_embeddings': True}
    )
    
    print("--- Loading Vector Store (Supabase)... ---")
    # This is the Vector Database from your diagram [cite: 32]
    app.state.vector_store = get_vector_store(app.state.embedding_model)
    
    print("--- Loading Narrative Synthesizer (Groq LLM)... ---")
    # This is the Narrative Synthesizer from your diagram [cite: 34]
    app.state.groq_llm = ChatGroq(
        temperature=0, 
        groq_api_key=os.getenv("GROQ_API_KEY"), 
        model_name="llama3-8b-8192" # Fast and capable model
    )
    print("--- Services loaded successfully. ---")
    # --- END NEW RAG COMPONENTS ---


@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources when the app shuts down."""
    if hasattr(app.state, 'db_connection') and app.state.db_connection:
        app.state.db_connection.close()
        print("--- Database connection closed. ---")

# --- Pydantic Model for API Request ---
# This class was missing, causing the NameError
class QueryRequest(BaseModel):
    nl_query: str
    page: int = 1


# --- API Endpoints ---

@app.get("/api/health")
async def check_service_health():
    """Health check endpoint to verify service is running."""
    # A simple health check for now
    return {"status": "ok", "services": ["nl_query_service"]}


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
    # This is the "simultaneously" step from your diagram [cite: 49]
    try:
        # Find the top 3 most similar documents
        vector_docs = vector_store.similarity_search(nl_query, k=3)
        # Format for the prompt
        vector_data = "\n---\n".join([doc.page_content for doc in vector_docs])
    except Exception as e:
        print(f"Vector search failed: {e}")
        vector_data = "No vector data found."

    # --- STEP 3: Synthesize Narrative ---
    print("Step 3: Synthesizing final narrative with Groq...")
    # This is the "Narrative Synthesizer" step [cite: 34]
    
    prompt = ChatPromptTemplate.from_template(NARRATIVE_SYNTHESIS_TEMPLATE)
    
    synthesis_chain = (
        prompt |
        groq_llm |
        StrOutputParser()
    )
    
    final_narrative = synthesis_chain.invoke({
        "question": nl_query,
        "sql_data": sql_response.get("results", "No SQL data found."), # Use .get for safety
        "vector_data": vector_data
    })
    
    print(f"Final Narrative: {final_narrative}")
    
    # --- STEP 4: Return Unified Response ---
    # This response now includes all parts of the RAG pipeline
    return {
        "success": True,
        "nl_query": nl_query,
        "nl_response": final_narrative, # The NEW synthesized answer
        "sql_query": sql_response.get("sql_query"),
        "sql_results": sql_response.get("results"),
        "vector_context": vector_data,
        "processing_method": sql_response.get("processing_method"),
        "execution_time": sql_response.get("execution_time") # Note: this is just SQL time
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

#--end-of-file--
