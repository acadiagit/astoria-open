// Filename: console/src/App.jsx
// Final version with pre-populated sample queries in the history.

import React, { useState, useEffect, useCallback } from 'react';
import { getHubStatus, submitQueryToHub } from './utils/api';

const serviceMap = [
    { key: 'supabase_vector', label: 'Supabase' },
    { key: 'google_gemini', label: 'Gemini' },
    { key: 'groq', label: 'Groq' }
];

// --- Service Status Component Logic ---
function ServiceStatus() {
    const [status, setStatus] = useState({});
    const [isLoading, setIsLoading] = useState(false);

    const updateAllStatuses = useCallback(async () => {
        setIsLoading(true);
        try {
            const data = await getHubStatus();
            setStatus(data);
        } catch (err) { console.error(err); }
        setIsLoading(false);
    }, []);

    useEffect(() => {
        updateAllStatuses();
    }, [updateAllStatuses]);
    
    return (
        <div className="status-container">
            <h3>External Service Status <button onClick={updateAllStatuses} disabled={isLoading}>{isLoading ? 'Checking...' : 'Refresh'}</button></h3>
            {serviceMap.map(service => {
                const state = status[service.key];
                const dotClass = state === 'OK' ? 'status-ok' : (state ? 'status-error' : 'status-unknown');
                return (
                    <div key={service.key} className="status-item">
                        <div className={`status-dot ${dotClass}`}></div>
                        <span>{`${service.label}: ${state || 'Unknown'}`}</span>
                    </div>
                );
            })}
        </div>
    );
}

// --- Main Query Console Component Logic ---
function QueryConsole() {
  // --- NEW: Define the list of sample queries ---
  const initialHistory = [
    { query: "List the names of 4 ships type brig", response: null },
    { query: "tell me all you know about the ship KODIAK", response: null },
    { query: "Show me name of the oldest ship", response: null },
    { query: "list the names of vessels built before 1780", response: null },
    { query: "List the names of that largest (longest ok) schooners and where they were built", response: null },
    { query: "show me the names of 10 crew members", response: null },
    { query: "List 2 voyages for the ship, KODIAK", response: null },
  ];

  const [query, setQuery] = useState('');
  const [response, setResponse] = useState(null);
  // --- CHANGED: Initialize history state with the sample queries ---
  const [history, setHistory] = useState(initialHistory);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const clearState = () => {
    setError(null);
    setResponse(null);
  };
  
  const renderSqlResults = (data) => {
    if (!data) return <p>No data available</p>;
    if (Array.isArray(data) && data.length > 0) {
        if (data.length === 1 && data[0].answer) return <p>{data[0].answer}</p>;
        const columns = Object.keys(data[0]);
        return (
            <div className="table-container">
                <table className="results-table">
                    <thead><tr>{columns.map(col => <th key={col}>{col.replace(/_/g, ' ')}</th>)}</tr></thead>
                    <tbody>{data.map((row, i) => <tr key={i}>{columns.map(col => <td key={col}>{String(row[col] ?? '')}</td>)}</tr>)}</tbody>
                </table>
            </div>
        );
    }
    return <pre>{JSON.stringify(data, null, 2)}</pre>;
  };
  
  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!query.trim()) return;
    setLoading(true);
    clearState();
    try {
      const data = await submitQueryToHub(query);
      if (data && data.status === 'success') {
        setResponse(data);
        setHistory(prev => [{ query, response: data }, ...prev.slice(0, 19)]);
      } else {
        setError(data.error || data.message || 'An unknown error occurred.');
      }
    } catch (err) {
      setError(`A connection error occurred. Please ensure the Hub is running.`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="console-container">
        <aside className="sidebar">
            <h2>Query History</h2>
            <div className="history-list">
                {history.map((item, index) => (
                    <div key={index} className="history-item" onClick={() => setQuery(item.query)}>
                        <p><strong>{item.query}</strong></p>
                    </div>
                ))}
            </div>
        </aside>
        <main className="main-content">
            <form onSubmit={handleSubmit}>
                <textarea
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    placeholder="e.g., How many ships are there?"
                    rows="3"
                />
                <button type="submit" disabled={loading}>
                    {loading ? 'Processing...' : 'Submit'}
                </button>
            </form>
            <div className="response-area">
                {loading && <p>Loading...</p>}
                {error && <div className="error-response"><strong>Error:</strong> {error}</div>}
                {response && <div className="query-response">
                    <h3>Narrative</h3>
                    <p>{response.narrative || "No narrative generated."}</p>
                    <h3>SQL Result</h3>
                    {renderSqlResults(response.results)}
                    <details>
                        <summary>Debug Info</summary>
                        <pre className="sql-code">{response.generated_sql}</pre>
                        <p>Processing Method: {response.processing_method}</p>
                    </details>
                </div>}
            </div>
        </main>
    </div>
  );
}

// --- Main App Component ---
function App() {
  return (
    <div>
        <header style={{ padding: '0 1rem', borderBottom: '1px solid #ddd', backgroundColor: 'white' }}>
            <h1>Astoria Open Query Console</h1>
        </header>
        <ServiceStatus />
        <QueryConsole />
    </div>
  );
}

export default App;
