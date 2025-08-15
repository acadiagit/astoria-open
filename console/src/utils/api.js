// Path: /src/utils/api.js

const API_BASE_URL = '';

export const getHubStatus = async () => {
  const endpoint = `${API_BASE_URL}/api/v1/status`;
  return await fetch(endpoint).then(res => res.json());
};

export const submitQueryToHub = async (query) => {
  const endpoint = `${API_BASE_URL}/api/v1/query`;
  const response = await fetch(endpoint, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query }),
  });
  if (!response.ok) {
    const errorBody = await response.text();
    throw new Error(`Network response was not ok: ${response.status} - ${errorBody}`);
  }
  return await response.json();
};
//end-of-file
