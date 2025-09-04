// Filename: src/utils/api.js
// Purpose: Handles all API calls from the React UI to the Python backend.

const API_BASE_URL = 'http://127.0.0.1:5001/api/v1';

/**
 * Submits a natural language query to the backend.
 * @param {string} query The user's question.
 * @param {number} page The page number for pagination.
 * @returns {Promise<object>} The JSON response from the server.
 */
export const submitQueryToHub = async (query, page = 1) => {
  try {
    const response = await fetch(`${API_BASE_URL}/query`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ query, page }),
    });

    if (!response.ok) {
      // Try to get a meaningful error from the server's response body
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.message || `HTTP error! Status: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error("API call to /query failed:", error);
    // Re-throw the error so the component can catch it and display it to the user
    throw error;
  }
};

/**
 * Checks the health of the backend server.
 * @returns {Promise<object>} The JSON response from the health endpoint.
 */
export const getHubStatus = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/health`);

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.message || `HTTP error! Status: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error("API call to /health failed:", error);
    throw error;
  }
};
