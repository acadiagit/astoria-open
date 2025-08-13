// Path: /src/App.jsx

import { useState } from 'react';
import { getHubStatus, submitQueryToHub } from './utils/api.js';

function App() {
  const [query, setQuery] = useState('');
  const [response, setResponse] = useState(null);
  const [history, setHistory] = useState([]); // Client-side history
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [diagResult, setDiagResult] = useState(null);

  const clearState = () => {
    setError(null);
    setResponse(null);
    setDiagResult(null);
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
        // Add successful query to the start of the history
        setHistory(prev => [{ query, response: data }, ...prev]);
      } else {
        setError(data.error || data.message || 'An unknown error occurred.');
      }
    } catch (err) {
      setError(`A connection error occurred. Please ensure the Hub is running.`);
    } finally {
      setLoading(false);
    }
  };

  const handleHealthCheck = async () => {
    setLoading(true);
    clearState();
    try {
      const data = await getHubStatus();
      setDiagResult({ type: 'Health Check', data });
    } catch (err) {
      setError('Health check failed. Ensure the Hub is running.');
    } finally {
      setLoading(false);
    }
  };

  const handleAgentCheck = async () => {
    setLoading(true);
    clearState();
    try {
      const data = await submitQueryToHub("List one vessel name.");
      setDiagResult({ type: 'Agent + DB Test', data });
    } catch (err) {
      setError('Agent/DB test failed. Ensure the Hub and all services are running correctly.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="console-container">
      <aside className="sidebar">
        <h2>Query History</h2>
        <div className="history-list">
          {history.length === 0 ? <p>No history yet.</p> : history.map((item, index) => (
            <div key={index} className="history-item" onClick={() => setResponse(item.response)}>
              <p>{item.query}</p>
            </div>
          ))}
        </div>
        <div className="diagnostics">
          <h2>Diagnostics</h2>
          <button onClick={handleHealthCheck}>Test Hub Health</button>
          <button onClick={handleAgentCheck}>Test Agent+DB</button>
        </div>
      </aside>

      <main className="main-content">
        <header>
          <h1>Astoria Console</h1>
        </header>
        
        <form onSubmit={handleSubmit}>
          <textarea
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Ask a maritime question..."
            rows="4"
            disabled={loading}
          />
          <button type="submit" disabled={loading}>
            {loading ? 'Processing...' : 'Submit Query'}
          </button>
        </form>

        <div className="response-area">
          {loading && <div className="loading">Processing...</div>}
          {error && <div className="error-response"><h3>Error</h3><pre>{error}</pre></div>}
          {diagResult && <div className="diag-response"><h3>Diagnostic Result</h3><pre>{JSON.stringify(diagResult, null, 2)}</pre></div>}
          {response && (
            <div>
              <h2>Response</h2>
              <pre className="nl-response">{response.nl_response}</pre>
              {response.generated_sql && (
                <>
                  <h3>Generated SQL</h3>
                  <pre className="sql-code">{response.generated_sql}</pre>
                  <h3>SQL Result</h3>
                  <pre>{JSON.stringify(response.database_results, null, 2)}</pre>
                </>
              )}
            </div>
          )}
        </div>
      </main>
    </div>
  );
}

export default App;
//end-of-file
