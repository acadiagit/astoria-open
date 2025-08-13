# Path: /astoria-stack/main.py
# Filename: main.py

import logging
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv
import os

# It's good practice to load this at the very start
load_dotenv()

from app.services.nl_query_service import process_nl_query

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- MODIFICATION FOR SERVING STATIC UI FILES ---
# Point to the build directory of our React app
app = Flask(__name__, static_folder='console/dist', static_url_path='/')
CORS(app)
# -----------------------------------------------

# --- HEALTH CHECK ENDPOINT ---
@app.route('/api/v1/status', methods=['GET'])
def get_status():
    """A simple endpoint to confirm the server is running."""
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

# --- NEW: ROUTE TO SERVE THE REACT APP ---
@app.route('/')
def serve():
    return send_from_directory(app.static_folder, 'index.html')

@app.errorhandler(404)
def not_found(e):
    return send_from_directory(app.static_folder, 'index.html')
# -----------------------------------------


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)

#end-of-file
