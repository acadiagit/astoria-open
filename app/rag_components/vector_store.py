# Path: /astoria_rag_hub/app/rag_components/vector_store.py
# Filename: vector_store.py

import os
import logging
from supabase.client import create_client, Client
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores.supabase import SupabaseVectorStore

logger = logging.getLogger(__name__)

# Define the name of the embeddings model we'll use
EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

def get_vector_store() -> SupabaseVectorStore:
    """
    Initializes and returns a Supabase vector store client.
    """
    logger.info("Initializing vector store...")
    
    # Get Supabase credentials from environment variables
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    
    if not supabase_url or not supabase_key:
        raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in the .env file.")
    
    # Initialize the Supabase client
    supabase_client: Client = create_client(supabase_url, supabase_key)
    logger.info("Supabase client initialized.")
    
    # Initialize the embeddings model from Hugging Face
    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL_NAME)
    logger.info(f"Embeddings model loaded: {EMBEDDING_MODEL_NAME}")
    
    # Initialize the LangChain vector store with Supabase
    vector_store = SupabaseVectorStore(
        client=supabase_client,
        embedding=embeddings,
        table_name="documents",      # The table in Supabase to store the vectors
        query_name="match_documents" # The Supabase RPC function to call for similarity search
    )
    logger.info("Supabase vector store initialized.")
    
    return vector_store

#end-of-file
