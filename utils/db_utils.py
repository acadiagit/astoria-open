# [utils/db_utils.py]
# Purpose: Provides database utility functions, including
#          schema retrieval and vector store initialization.

import os
import psycopg2
from dotenv import load_dotenv
from langchain_community.vectorstores import SupabaseVectorStore
from supabase.client import create_client, Client

# Load environment variables from .env file
load_dotenv()

def get_db_connection():
    """Establishes and returns a direct psycopg2 database connection."""
    try:
        connection = psycopg2.connect(
            user=os.getenv('POSTGRES_USER'),
            password=os.getenv('POSTGRES_PASSWORD'),
            host=os.getenv('POSTGRES_HOST'),
            port=os.getenv('POSTGRES_PORT'),
            dbname=os.getenv('POSTGRES_DB')
        )
        return connection
    except Exception as e:
        print(f"Error connecting to the database: {e}")
        raise

def get_schema(connection):
    """
    Retrieves a simplified schema of the public tables in the database.
    This is used by the NL2SQL service to understand the data structure.
    """
    schema = {}
    with connection.cursor() as cursor:
        # Get all tables in the public schema
        cursor.execute("""
            SELECT tablename 
            FROM pg_catalog.pg_tables 
            WHERE schemaname != 'pg_catalog' AND schemaname != 'information_schema';
        """)
        tables = [row[0] for row in cursor.fetchall()]
        
        # For each table, get its columns and data types
        for table_name in tables:
            cursor.execute(f"""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = '{table_name}';
            """)
            columns = {row[0]: row[1] for row in cursor.fetchall()}
            schema[table_name] = columns
            
    return schema

# --- NEW FUNCTION (This was missing/corrupted) ---
def get_vector_store(embedding_model):
    """
    Initializes and returns a SupabaseVectorStore instance.
    This is required by main.py to power the RAG search.
    """
    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_key = os.environ.get("SUPABASE_KEY")
    
    if not supabase_url or not supabase_key:
        raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in .env")

    # Initialize a Supabase client (needed by the vector store)
    supabase_client: Client = create_client(supabase_url, supabase_key)
    
    # --- IMPORTANT ---
    # These names MUST match your Supabase vector table
    # and your SQL search function.
    TABLE_NAME = "documents"
    FUNCTION_NAME = "match_documents"
    
    vector_store = SupabaseVectorStore(
        client=supabase_client,
        embedding=embedding_model,
        table_name=TABLE_NAME,
        query_name=FUNCTION_NAME
    )
    
    return vector_store
# --- END NEW FUNCTION ---

if __name__ == '__main__':
    # For testing the connection and schema retrieval directly
    print("Testing database connection and schema retrieval...")
    try:
        conn = get_db_connection()
        db_schema = get_schema(conn)
        print("Schema retrieved successfully:")
        for table, cols in db_schema.items():
            print(f"- Table: {table}")
            for col, dtype in cols.items():
                print(f"  - {col}: {dtype}")
        conn.close()
    except Exception as e:
        print(f"Test failed: {e}")

#--end-of-file--
