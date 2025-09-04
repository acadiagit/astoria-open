# Filename: main.py
# Purpose: Main Flask application with a universal, versioned API endpoint.
# Last Modified: August 28, 2025

import logging
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

# Import the core processing function from our service layer
from app.services.nl_query_service import process_nl_query, _initialize_services

# --- Basic Setup ---
load_dotenv()
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
app = Flask(__name__)
CORS(app) # Enable Cross-Origin Resource Sharing

# --- API Endpoints (Version 1) ---

@app.route('/api/v1/health', methods=['GET'])
def health_check():
    """A simple health check endpoint for any UI's diagnostic button."""
    return jsonify({'status': 'ok', 'message': 'Astoria backend is running.'})

@app.route('/api/v1/query', methods=['POST'])
def query():
    """Main endpoint to process a natural language query."""
    data = request.get_json()
    if not data or 'query' not in data:
        return jsonify({'status': 'error', 'message': 'JSON body with "query" key is required.'}), 400
    
    nl_query = data.get('query')
    page = data.get('page', 1)
    
    try:
        page = int(page)
        if page < 1: page = 1
    except (ValueError, TypeError):
        page = 1

    result = process_nl_query(nl_query, page=page)
    
    return jsonify(result)

# --- Main Application Runner ---

if __name__ == '__main__':
    try:
        _initialize_services()
        logging.info("All services initialized successfully.")
    except Exception as e:
        logging.error(f"FATAL: Could not initialize services on startup: {e}", exc_info=True)
    
    app.run(host='0.0.0.0', port=5001, debug=True)

#--end-of-file
