import React, { useState } from 'react';
import { text2sqlAPI } from '../../utils/api';
import './Text2SQL.css';

const Text2SQL = () => {
  const [question, setQuestion] = useState('');
  const [topK, setTopK] = useState(3);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!question.trim() || loading) return;

    setLoading(true);
    setError('');
    setResult(null);

    try {
      const response = await text2sqlAPI.query(question.trim(), topK);
      setResult(response.data);
    } catch (err) {
      if (err.response?.status === 429 || err.response?.data?.detail?.includes('quota')) {
        setError('Out of Message Quota - Please try again later');
      } else {
        setError(err.response?.data?.detail || 'Failed to process query');
      }
    } finally {
      setLoading(false);
    }
  };

  const renderResults = () => {
    if (!result?.results || result.results.length === 0) {
      return <div className="no-results">No results found</div>;
    }

    const columns = Object.keys(result.results[0]);
    
    return (
      <div className="results-container">
        <div className="sql-query">
          <h4>Generated SQL Query:</h4>
          <pre className="sql-code">{result.sql_query}</pre>
        </div>
        
        <div className="results-table">
          <h4>Results ({result.results.length} rows):</h4>
          <table className="data-table">
            <thead>
              <tr>
                {columns.map(col => (
                  <th key={col}>{col}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {result.results.map((row, idx) => (
                <tr key={idx}>
                  {columns.map(col => (
                    <td key={col}>{row[col]?.toString() || 'N/A'}</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    );
  };

  return (
    <div className="text2sql-container">
      <h2 className="text2sql-title">Natural Language to SQL</h2>
      <p className="text2sql-subtitle">
        Ask questions about your claims data in natural language
      </p>

      {error && <div className="error-message">{error}</div>}

      <form onSubmit={handleSubmit} className="text2sql-form">
        <div className="form-group">
          <label htmlFor="question">Your Question:</label>
          <textarea
            id="question"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="e.g., How many claims are denied? What's the average billed amount?"
            className="question-input"
            disabled={loading}
            rows={3}
          />
        </div>
        
        <div className="form-group">
          <label htmlFor="topK">Query Retries (top_k):</label>
          <input
            type="number"
            id="topK"
            value={topK}
            onChange={(e) => setTopK(parseInt(e.target.value))}
            min="1"
            max="10"
            className="topk-input"
            disabled={loading}
          />
        </div>

        <button
          type="submit"
          disabled={loading || !question.trim()}
          className="query-button"
        >
          {loading ? 'Processing...' : 'Run Query'}
        </button>
      </form>

      {result && renderResults()}
    </div>
  );
};

export default Text2SQL;
