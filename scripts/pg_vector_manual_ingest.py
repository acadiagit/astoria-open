# Path: /astoria_rag_hub/scripts/pg_vector_manual_ingest.py
# Filename: pg_vector_manual_ingest.py

import os
import sys
import json
import logging
import math
import requests
from dotenv import load_dotenv

# Add the root directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from app.rag_components.data_loader import load_documents_from_directory

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def manual_ingest():
    """
    Loads, splits, embeds, and manually uploads documents using the requests library.
    """
    load_dotenv()
    
    # --- 1. Load Documents from files ---
    logging.info("Loading documents from directory...")
    documents = load_documents_from_directory('data/maritime_history')
    if not documents:
        logging.warning("No documents found. Exiting.")
        return

    # --- 2. Split documents into smaller chunks ---
    logging.info("Splitting documents...")
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    chunks = text_splitter.split_documents(documents)
    logging.info(f"Split {len(documents)} documents into {len(chunks)} chunks.")

    # --- 3. Create Embeddings for each chunk ---
    logging.info("Initializing embedding model...")
    model_name = "sentence-transformers/all-MiniLM-L6-v2"
    embeddings_model = HuggingFaceEmbeddings(model_name=model_name)

    logging.info("Creating embeddings for all chunks...")
    all_embeddings = embeddings_model.embed_documents([chunk.page_content for chunk in chunks])
    logging.info("Embeddings created.")

    # --- 4. Prepare data payloads for upload ---
    payloads = []
    for i, chunk in enumerate(chunks):
        payloads.append({
            "content": chunk.page_content,
            "metadata": chunk.metadata,
            "embedding": all_embeddings[i]
        })

    # --- 5. Upload data in batches using requests ---
    logging.info("Preparing to upload data in batches...")
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    api_url = f"{url}/rest/v1/documents" # Target the 'documents' table
    headers = {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "Prefer": "return=representation"
    }

    batch_size = 50
    num_batches = math.ceil(len(payloads) / batch_size)

    for i in range(0, len(payloads), batch_size):
        batch_num = (i // batch_size) + 1
        batch = payloads[i:i + batch_size]
        logging.info(f"Uploading batch {batch_num}/{num_batches}...")
        
        try:
            response = requests.post(api_url, headers=headers, data=json.dumps(batch))
            response.raise_for_status() # Raises an error for bad status codes (4xx or 5xx)
            logging.info(f"Batch {batch_num} uploaded successfully. Status: {response.status_code}")
        except requests.exceptions.RequestException as e:
            logging.error(f"Failed to upload batch {batch_num}. Error: {e}")
            break # Stop on failure

    logging.info("✅ Manual ingestion process completed!")


if __name__ == "__main__":
    manual_ingest()

#end-of-file
