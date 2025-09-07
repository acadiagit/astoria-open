// Filename: console/src/utils/api.js
// Purpose: Handles all API calls from the React UI to the Python backend.

/**
 * Submits a natural language query to the backend.
 * @param {string} query The user's question.
 * @param {number} page The page number for pagination.
 * @returns {Promise<object>} The JSON response from the server.
 */
export async function submitQueryToHub(query, page = 1) {
    // This uses the Vite proxy to send the request to your backend at port 8000
    const response = await fetch('/api/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ nl_query: query, page }), // Match backend expectation
    });
    if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.message || `HTTP error! Status: ${response.status}`);
    }
    return response.json();
}

/**
 * Fetches the health status of external services from the backend.
 * @returns {Promise<object>} The health status object.
 */
export async function getHubStatus() {
    // This uses the Vite proxy to send the request to your backend at port 8000
    const response = await fetch('/api/health');
    if (!response.ok) {
        throw new Error(`Failed to fetch service status`);
    }
    return response.json();
}

// -- end of file --
