// Path: console/src/App.jsx
// File: App.jsx
// Execute from: /Users/hugodiaz/Astoria/hf_spaces/astoria_open/console
// Command: cp App.jsx src/App.jsx (from project root)

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

  // Function to properly render SQL results
  const renderSqlResults = (data) => {
    console.log('Raw data received:', data); // Debug log
    
    if (!data) {
      return (
        <div className="no-results">
          <p>No data available</p>
        </div>
      );
    }

    // If data is a string, display it directly
    if (typeof data === 'string') {
      return (
        <div className="text-result">
          <pre>{data}</pre>
        </div>
      );
    }

    // If data is an array
    if (Array.isArray(data)) {
      if (data.length === 0) {
        return (
          <div className="no-results">
            <p>No results found</p>
          </div>
        );
      }

      // Handle count queries (single number result)
      if (data.length === 1 && data[0].count !== undefined) {
        return (
          <div className="count-result">
            <div className="count-number">{data[0].count.toLocaleString()}</div>
            <div className="count-label">Total Count</div>
          </div>
        );
      }

      // Handle table data - create a proper table
      const columns = Object.keys(data[0]);
      return (
        <div className="table-container">
          <div className="results-summary">
            Showing {data.length} result{data.length !== 1 ? 's' : ''}
          </div>
          <table className="results-table">
            <thead>
              <tr>
                {columns.map(col => (
                  <th key={col}>{col.replace(/_/g, ' ').toUpperCase()}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {data.map((row, index) => (
                <tr key={index}>
                  {columns.map(col => (
                    <td key={col}>
                      {row[col] !== null && row[col] !== undefined ? 
                        String(row[col]) : 
                        <span className="null-value">—</span>
                      }
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      );
    }

    // If data is an object
    if (typeof data === 'object') {
      return (
        <div className="object-result">
          {Object.entries(data).map(([key, value]) => (
            <div key={key} className="key-value-pair">
              <span className="key">{key.replace(/_/g, ' ')}:</span>
              <span className="value">{String(value)}</span>
            </div>
          ))}
        </div>
      );
    }

    // Fallback - display as formatted JSON
    return (
      <div className="json-result">
        <pre>{JSON.stringify(data, null, 2)}</pre>
      </div>
    );
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!query.trim()) return;
    setLoading(true);
    clearState();
    
    try {
      const data = await submitQueryToHub(query);
      console.log('Full API response:', data); // Debug log
      
      if (data && data.status === 'success') {
        setResponse(data);
        // Add successful query to the start of the history
        setHistory(prev => [{ query, response: data }, ...prev]);
      } else {
        setError(data.error || data.message || 'An unknown error occurred.');
      }
    } catch (err) {
      console.error('Query error:', err); // Debug log
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
          {diagResult && (
            <div className="diag-response">
              <h3>Diagnostic Result</h3>
              <pre>{JSON.stringify(diagResult, null, 2)}</pre>
            </div>
          )}
          {response && (
            <div className="query-response">
              <h2>Response</h2>
              <div className="response-summary">
                <strong>{response.nl_response}</strong>
              </div>
              
              {response.generated_sql && (
                <>
                  <h3>Generated SQL</h3>
                  <pre className="sql-code">{response.generated_sql}</pre>
                  
                  <h3>SQL Results</h3>
                  <div className="sql-results">
                    {renderSqlResults(response.results)}
                  </div>
                  
                  {/* Debug info - show available fields */}
                  <details className="debug-info">
                    <summary>Debug Info</summary>
                    <div className="debug-content">
                      <p><strong>Available fields:</strong> {Object.keys(response).join(', ')}</p>
                      <p><strong>Processing method:</strong> {response.processing_method}</p>
                      <p><strong>Execution time:</strong> {response.execution_time?.toFixed(3)}s</p>
                      <p><strong>Confidence:</strong> {(response.confidence * 100)?.toFixed(1)}%</p>
                      {response.warnings?.length > 0 && (
                        <p><strong>Warnings:</strong> {response.warnings.join(', ')}</p>
                      )}
                    </div>
                  </details>
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
//end-of-script