# Filename: app/services/nl_query_service.py
# Purpose: Definitive version with a router to select between the direct chain and the agent.

import logging
import os
import re
import requests
import time
from typing import List, Dict, Any, Optional
from types import SimpleNamespace

# LangChain Imports
from langchain.chains import create_sql_query_chain
from langchain_community.utilities import SQLDatabase
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_groq import ChatGroq
from langchain_google_genai import ChatGoogleGenerativeAI
from google.api_core.exceptions import GoogleAPICallError

# SQLAlchemy import for direct execution
from sqlalchemy import text, create_engine

# Import the agent from its setup file
from app.rag_components.agent_setup import create_maritime_agent

os.environ["TOKENIZERS_PARALLELISM"] = "false"
logger = logging.getLogger(__name__)

# --- Global Services ---
_db = None
_google_llm = None
_llm_groq = None
_embeddings_model = None
_agent_executor = None
_health_status_cache = {"status": {}, "last_checked": 0}

def _initialize_services():
    """Initializes all necessary services on startup."""
    global _db, _google_llm, _llm_groq, _embeddings_model, _agent_executor
    
    if not _db:
        from dotenv import load_dotenv
        load_dotenv()
        db_uri = f"postgresql+psycopg2://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}@{os.getenv('POSTGRES_HOST')}:{os.getenv('POSTGRES_PORT')}/{os.getenv('POSTGRES_DB')}"
        db_engine = create_engine(db_uri)
        _db = SQLDatabase(db_engine)
        logger.info("SQLDatabase service initialized.")

    if not _google_llm:
        _google_llm = ChatGoogleGenerativeAI(model="gemini-1.5-pro-latest", google_api_key=os.getenv("GOOGLE_API_KEY"), temperature=0)
        logger.info("Google Gemini LLM initialized.")
    
    if not _llm_groq:
        _llm_groq = ChatGroq(model_name="llama-3.1-8b-instant", groq_api_key=os.getenv('GROQ_API_KEY'), temperature=0.3)
    if not _embeddings_model:
        _embeddings_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

    if not _agent_executor:
        _agent_executor = create_maritime_agent()
        logger.info("Gemini SQL Agent Executor initialized.")

def _check_gemini_status():
    try:
        _google_llm.invoke("health check")
        return 'OK'
    except GoogleAPICallError as e:
        logger.warning(f"Health Check Error (Google Gemini): {e}")
        return 'Error'

def _check_groq_status():
    try:
        _llm_groq.invoke("health check")
        return 'OK'
    except Exception as e:
        logger.warning(f"Health Check Error (Groq): {e}")
        return 'Error'

def _check_supabase_status():
    """ A more robust health check that makes an authenticated request. """
    try:
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_KEY')
        
        test_url = f"{supabase_url}/rest/v1/"
        headers = {"apikey": supabase_key, "Authorization": f"Bearer {supabase_key}"}
        
        response = requests.get(test_url, headers=headers, timeout=5)
        response.raise_for_status()
        return 'OK'
    except Exception as e:
        logger.warning(f"Health Check Error (Supabase): {e}")
        return 'Error'

def check_service_health(service_name: Optional[str] = None) -> Dict[str, str]:
    global _health_status_cache
    _initialize_services()
    if not service_name and time.time() - _health_status_cache["last_checked"] < 60:
        return _health_status_cache["status"]
    status = {}
    check_map = {'google_gemini': _check_gemini_status, 'groq': _check_groq_status, 'supabase_vector': _check_supabase_status}
    if service_name and service_name in check_map:
        status[service_name] = check_map[service_name]()
    else:
        for name, func in check_map.items():
            status[name] = func()
        _health_status_cache = {"status": status, "last_checked": time.time()}
    logger.info(f"Health check for '{service_name or 'all'}' complete: {status}")
    return status

def run_sql_chain_manually(nl_query: str, page: int = 1) -> SimpleNamespace:
    logger.info(f"Invoking Gemini chain for page {page}...")
    sql_query_generated = ""
    try:
        write_query_chain = create_sql_query_chain(_google_llm, _db)
        sql_query_generated = write_query_chain.invoke({"question": nl_query})
        cleaned_sql = sql_query_generated.strip().strip("```sql").strip("```").strip()
        if "SELECT" in cleaned_sql.upper():
            cleaned_sql = cleaned_sql[cleaned_sql.upper().find("SELECT"):]
        cleaned_sql = cleaned_sql.strip().rstrip(';')
        pagination_applied = "limit" not in cleaned_sql.lower()
        limit = 20
        offset = (page - 1) * limit
        final_sql_query = f"{cleaned_sql} LIMIT {limit} OFFSET {offset}" if pagination_applied else cleaned_sql
        with _db._engine.connect() as connection:
            result_proxy = connection.execute(text(final_sql_query))
            results = [dict(zip(result_proxy.keys(), row)) for row in result_proxy.fetchall()]
        return SimpleNamespace(success=True, sql_query=final_sql_query, results=results, processing_method="llm_gemini_chain", pagination_applied=pagination_applied)
    except Exception as e:
        logger.error(f"Gemini SQL chain failed: {e}", exc_info=True)
        return SimpleNamespace(success=False, errors=[str(e)], sql_query=sql_query_generated, results=[])

def search_vector_database(query: str, limit: int = 5) -> List[Dict[str, Any]]:
    try:
        query_embedding = _embeddings_model.embed_query(query)
        rpc_url = f"{os.getenv('SUPABASE_URL')}/rest/v1/rpc/search_documents"
        headers = {"apikey": os.getenv('SUPABASE_KEY'), "Authorization": f"Bearer {os.getenv('SUPABASE_KEY')}"}
        payload = {"query_embedding": query_embedding, "match_threshold": 0.5, "match_count": limit}
        response = requests.post(rpc_url, headers=headers, json=payload, timeout=10)
        return response.json() if response.ok else []
    except Exception as e:
        logger.error(f"Vector search error: {e}")
        return []

def generate_narrative_response(user_query, sql_results, vector_context, sql_query):
    prompt = f"User Query: {user_query}\nSQL Data: {sql_results[:3]}\nVector Context: {vector_context}\nSynthesize a brief narrative."
    response = _llm_groq.invoke(prompt)
    return response.content.strip()

def process_nl_query(nl_query: str, page: int = 1):
    logger.info(f"Processing full query: '{nl_query}' for page {page}")
    _initialize_services()
    health = check_service_health()
    if health.get('google_gemini') == 'Error':
        return {'status': 'error', 'nl_query': nl_query, 'message': "Core service (Google Gemini) is currently unavailable."}

    agent_keywords = ["analyze", "compare", "what is the best", "find the relationship", "what kind of data"]
    if any(keyword in nl_query.lower() for keyword in agent_keywords):
        logger.info("Complex query detected. Routing to Gemini SQL Agent.")
        try:
            agent_result = _agent_executor.invoke({"input": nl_query})
            final_answer = agent_result.get("output", "Agent did not provide a final answer.")
            return {'status': 'success', 'nl_query': nl_query, 'generated_sql': "N/A (Handled by Agent)", 'processing_method': "llm_gemini_agent", 'results': [{"answer": final_answer}], 'narrative': "", 'page': 1, 'has_more_results': False}
        except Exception as e:
            logger.error(f"Gemini Agent failed: {e}", exc_info=True)
            return {'status': 'error', 'nl_query': nl_query, 'message': f"The agent encountered an error: {e}"}
    else:
        logger.info("Simple query detected. Routing to direct Gemini SQL chain.")
        result = run_sql_chain_manually(nl_query, page=page)
        if not result.success:
            return {'status': 'error', 'nl_query': nl_query, 'message': "Failed to process SQL query.", 'errors': result.errors}
        narrative = ""
        if page == 1:
            health = check_service_health()
            vector_context = []
            if health.get('supabase_vector') == 'OK':
                vector_context = search_vector_database(nl_query)
            if health.get('groq') == 'OK':
                narrative = generate_narrative_response(user_query=nl_query, sql_results=result.results, vector_context=vector_context, sql_query=result.sql_query or "")
            else:
                narrative = "Narrative generation is temporarily unavailable."
        return {'status': 'success', 'nl_query': nl_query, 'generated_sql': result.sql_query, 'processing_method': result.processing_method, 'results': result.results, 'narrative': narrative, 'page': page, 'has_more_results': len(result.results) == 20 and result.pagination_applied}

# -- end of file --
