# Filename: app/services/nl_query_service.py
# Purpose: Definitive version with smart pagination and full RAG capabilities.
# Last Modified: September 3, 2025 (Gemini Integration)

import logging
import os
import re
import requests
from typing import List, Dict, Any
from types import SimpleNamespace

# LangChain Imports
from langchain.chains import create_sql_query_chain
from langchain_community.utilities import SQLDatabase
from langchain_community.chat_models import ChatOllama 
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_groq import ChatGroq
# --- CHANGE: Added Gemini Import ---
from langchain_google_genai import ChatGoogleGenerativeAI

# SQLAlchemy import for direct execution
from sqlalchemy import text

os.environ["TOKENIZERS_PARALLELISM"] = "false"
logger = logging.getLogger(__name__)

# --- Global Services ---
_embeddings_model = None
_llm_groq = None
_db = None

def _initialize_services():
    """Initializes all necessary services on startup."""
    global _embeddings_model, _llm_groq, _db
    
    if _db is None:
        from dotenv import load_dotenv
        from sqlalchemy import create_engine
        load_dotenv()
        
        db_uri = f"postgresql+psycopg2://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}@{os.getenv('POSTGRES_HOST')}:{os.getenv('POSTGRES_PORT')}/{os.getenv('POSTGRES_DB')}"
        db_engine = create_engine(db_uri)
        _db = SQLDatabase(db_engine)
        logger.info("SQLDatabase service initialized.")

    if _embeddings_model is None:
        _embeddings_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
        logger.info("Embeddings model initialized.")
    
    if _llm_groq is None:
        _llm_groq = ChatGroq(model_name="llama3-8b-8192", groq_api_key=os.getenv('GROQ_API_KEY'), temperature=0.3)
        logger.info("Groq LLM for narrative initialized.")

def run_sql_chain_manually(nl_query: str, page: int = 1) -> SimpleNamespace:
    """
    Generates and executes SQL with smart pagination logic.
    """
    logger.info(f"Invoking Gemini chain for page {page}...")
    try:
        # --- CHANGE: Swapped Ollama for Gemini ---
        # Old line: llm = ChatOllama(model="codellama", temperature=0)
        llm = ChatGoogleGenerativeAI(model="gemini-1.5-pro-latest", google_api_key=os.getenv("GOOGLE_API_KEY"), temperature=0)
        # ----------------------------------------
        
        write_query_chain = create_sql_query_chain(llm, _db)
        sql_query_generated = write_query_chain.invoke({"question": nl_query})

        # --- Smart Cleaning & Pagination Logic ---
        cleaned_sql = sql_query_generated.strip()
        if cleaned_sql.startswith("```"):
            cleaned_sql = '\n'.join(cleaned_sql.split('\n')[1:-1])
        
        cleaned_sql = cleaned_sql.strip().rstrip(';')
        
        # Check if the AI generated its own LIMIT clause
        pagination_applied = False
        if "limit" in cleaned_sql.lower():
            # The AI specified a limit, so we respect user intent
            final_sql_query = cleaned_sql
            logger.info("AI-generated LIMIT detected. Executing query as-is.")
        else:
            # The AI did not specify a limit, apply our pagination
            pagination_applied = True
            limit = 20
            offset = (page - 1) * limit
            final_sql_query = f"{cleaned_sql} LIMIT {limit} OFFSET {offset}"
        
        logger.info(f"Executing SQL: {final_sql_query}")
        
        with _db._engine.connect() as connection:
            result_proxy = connection.execute(text(final_sql_query))
            column_names = list(result_proxy.keys())
            raw_results = result_proxy.fetchall()
            final_results_list = [dict(zip(column_names, row)) for row in raw_results]
        
        logger.info(f"Query executed successfully. Found {len(final_results_list)} results.")
        return SimpleNamespace(
            success=True, 
            sql_query=final_sql_query, 
            results=final_results_list, 
            processing_method="llm_gemini_chain", # Updated processing method
            pagination_applied=pagination_applied
        )

    except Exception as e:
        logger.error(f"Gemini SQL chain failed: {e}", exc_info=True)
        return SimpleNamespace(success=False, errors=[str(e)], sql_query=None, results=[])

def search_vector_database(query: str, limit: int = 5) -> List[Dict[str, Any]]:
    """Searches the vector database for relevant unstructured documents."""
    try:
        query_embedding = _embeddings_model.embed_query(query)
        supabase_url, supabase_key = os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY')
        rpc_url = f"{supabase_url}/rest/v1/rpc/search_documents"
        headers = {"apikey": supabase_key, "Authorization": f"Bearer {supabase_key}", "Content-Type": "application/json"}
        payload = {"query_embedding": query_embedding, "match_threshold": 0.5, "match_count": limit}
        response = requests.post(rpc_url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            results = response.json()
            logger.info(f"Found {len(results)} relevant documents from vector search.")
            return results
        return []
    except Exception as e:
        logger.error(f"Vector search error: {e}")
        return []

def generate_narrative_response(user_query: str, sql_results: List[Dict[str, Any]], vector_context: List[Dict[str, Any]], sql_query: str) -> str:
    """Generates a final, credible narrative response using Groq Llama3."""
    if not sql_results and not vector_context:
        return "I could not find any information matching your query in the database."
    try:
        sql_summary = "No results found in the structured database."
        if sql_results:
            sql_summary = f"The database query returned {len(sql_results)} records."
        
        vector_summary = "No additional context was found in the document library."
        if vector_context:
            vector_summary = f"Found {len(vector_context)} relevant documents providing additional context."

        prompt = f"""You are a professional maritime data analyst. Your job is to synthesize data from two sources: a structured database and a document library. Provide a factual, credible, and concise response based ONLY on the provided data.

User Query: "{user_query}"

Source 1: Structured Database Query
- SQL Query Executed: {sql_query}
- Summary: {sql_summary}
- Data Sample: {str(sql_results[:3])}

Source 2: Document Library (Vector Search)
- Summary: {vector_summary}
- Context: {' '.join([doc.get('content', '') for doc in vector_context])[:1000]}

Synthesize a professional, 2-3 sentence narrative response based on the combined information. Do not mention the source names (e.g., "Source 1"). Just state the facts. If no data is found, say so.
"""
        response = _llm_groq.invoke(prompt)
        narrative = response.content.strip()
        logger.info("Generated credible narrative response successfully.")
        return narrative
    except Exception as e:
        logger.error(f"Narrative generation error: {e}")
        return "I found data in the database but encountered an issue providing a summary."

def process_nl_query(nl_query: str, page: int = 1):
    """Top-level function to process a query, including vector search and narrative generation."""
    logger.info(f"Processing full query: '{nl_query}' for page {page}")
    _initialize_services()
    
    result = run_sql_chain_manually(nl_query, page=page)

    if not result.success:
        return {'status': 'error', 'nl_query': nl_query, 'message': "Failed to process SQL query.", 'errors': result.errors}

    narrative = ""
    # The narrative and vector search should only be generated for the first page.
    if page == 1:
        vector_context = search_vector_database(nl_query)
        narrative = generate_narrative_response(
            user_query=nl_query,
            sql_results=result.results,
            vector_context=vector_context,
            sql_query=result.sql_query or ""
        )

    return {
        'status': 'success',
        'nl_query': nl_query,
        'generated_sql': result.sql_query,
        'processing_method': result.processing_method,
        'results': result.results,
        'narrative': narrative,
        'page': page,
        # The "More..." button should only appear if our application applied pagination
        'has_more_results': len(result.results) == 20 and result.pagination_applied
    }

#--end-of-file
