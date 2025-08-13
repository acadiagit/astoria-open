# Path: /astoria_rag_hub/main.py

import logging
from flask import Flask, request, jsonify
from flask_cors import CORS # <-- 1. Import CORS
from dotenv import load_dotenv

load_dotenv()

from app.services.nl_query_service import process_nl_query

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = Flask(__name__)
CORS(app) # <-- 2. Enable CORS for the entire app

# --- HEALTH CHECK ENDPOINT ---
@app.route('/api/v1/status', methods=['GET'])
def get_status():
    """A simple endpoint to confirm the server is running."""
    # <-- 3. Add a simple print statement to create a trail
    print("Health check endpoint was hit!") 
    return jsonify({"status": "ok", "message": "Astoria RAG Hub is running."})
# ------------------------------------

@app.route('/api/v1/query', methods=['POST'])
def handle_query():
    """API endpoint to handle natural language queries."""
    if not request.json or 'query' not in request.json:
        return jsonify({"error": "Query not provided"}), 400
    
    query = request.json['query']
    result = process_nl_query(query)
    
    return jsonify(result)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)

#end-of-file
