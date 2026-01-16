# Filename: utils/supabase_tester.py
# Purpose: A minimal script to test the Supabase vector search functionality.

import os
import requests
from dotenv import load_dotenv
from langchain_huggingface import HuggingFaceEmbeddings

def test_supabase_search():
    """
    Initializes an embedding model, creates a test vector, and calls the
    Supabase RPC function to test the entire vector search flow.
    """
    print("--- Testing Supabase Vector Search... ---")
    try:
        print("1. Loading environment variables from .env file...")
        load_dotenv()

        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_KEY")

        if not supabase_url or not supabase_key:
            print("🛑 ERROR: SUPABASE_URL or SUPABASE_KEY not found in .env file.")
            return

        print("2. Initializing sentence-transformer embedding model...")
        embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
        
        test_query = "What is a schooner?"
        print(f"3. Creating embedding for test query: '{test_query}'")
        query_embedding = embeddings.embed_query(test_query)

        rpc_url = f"{supabase_url}/rest/v1/rpc/search_documents"
        headers = {
            "apikey": supabase_key,
            "Authorization": f"Bearer {supabase_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "query_embedding": query_embedding,
            "match_threshold": 0.5,
            "match_count": 5
        }

        print(f"4. Sending POST request to: {rpc_url}")
        response = requests.post(rpc_url, headers=headers, json=payload, timeout=15)

        print(f"5. Received response with Status Code: {response.status_code}")
        
        if response.status_code == 200:
            results = response.json()
            print("✅ SUCCESS: Supabase vector search is available and responded.")
            print(f"Found {len(results)} documents.")
        else:
            print("🛑 FAILURE: Supabase API returned a non-200 status code.")
            print("Error details:", response.text)

    except Exception as e:
        print(f"🛑 FAILURE: An unexpected error occurred.")
        print(f"Error details: {e}")

if __name__ == "__main__":
    test_supabase_search()

# -- end of file --
