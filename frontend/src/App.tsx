import { useState } from "react";
import "./App.css";

type SummaryResponse = {
  summary: string;
};

type ErrorResponse = {
  detail?: string;
};

type HistoryItem = {
  id: number;
  input: string;
  output: string;
  created_at: string;
};

const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

function App() {
  const [text, setText] = useState("");
  const [summary, setSummary] = useState("");
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [isHistoryLoading, setIsHistoryLoading] = useState(false);
  const [historyError, setHistoryError] = useState("");

  async function getErrorMessage(response: Response) {
    try {
      const errorData: ErrorResponse = await response.json();

      if (errorData.detail) {
        return errorData.detail;
      }
    } catch {
      // Server response was not JSON.
    }

    return `Request failed with status ${response.status}.`;
  }

  async function loadHistory() {
    setIsHistoryLoading(true);
    setHistoryError("");

    try {
      const response = await fetch(`${API_URL}/history?limit=10`);

      if (!response.ok) {
        const message = await getErrorMessage(response);
        throw new Error(message);
      }

      const data: HistoryItem[] = await response.json();
      setHistory(data);
    } catch (requestError) {
      console.error(requestError);

      setHistoryError(
        requestError instanceof Error
          ? requestError.message
          : "Previous summaries could not be loaded.",
      );
    } finally {
      setIsHistoryLoading(false);
    }
  }

  async function handleSummarise() {
    if (!text.trim() || isLoading) {
      return;
    }

    setIsLoading(true);
    setError("");
    setSummary("");

    try {
      const response = await fetch(`${API_URL}/summarise`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          text: text,
        }),
      });

      if (!response.ok) {
        throw new Error(`Request failed with status ${response.status}`);
      }

      const data: SummaryResponse = await response.json();

      setSummary(data.summary);
      await loadHistory();
    } catch (requestError) {
      console.error(requestError);

      setError(
        requestError instanceof Error
          ? requestError.message
          : "The summary could not be generated. Check that the backend is running.",
      );
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <main className="app">
      {/* SUMMARY SECTION */}
      <section className="summary-card">
        <header className="page-header">
          <h1>MindCache</h1>
          <p>Turn long text into a clear, concise summary.</p>
        </header>

        <label htmlFor="summary-input">Text to summarise</label>

        <textarea
          id="summary-input"
          value={text}
          onChange={(event) => setText(event.target.value)}
          maxLength={1000}
          placeholder="Paste your text here..."
          rows={12}
        />

        <div className="input-footer">
          <span>{text.length}/1000</span>

          <button
            type="button"
            disabled={!text.trim() || isLoading}
            onClick={handleSummarise}
          >
            {isLoading ? "Summarising..." : "Summarise"}
          </button>
        </div>

        {error && (
          <section className="message error-message" role="alert">
            {error}
          </section>
        )}

        {summary && (
          <section className="result">
            <h2>Summary</h2>
            <p>{summary}</p>
          </section>
        )}
      </section>

      {/* HISTORY SECTION */}
      <section className="history-card">
        <div className="history-header">
          <div>
            <h2>Previous summaries</h2>
            <p>Your ten most recent results.</p>
          </div>

          <button className="secondary-button" type="button" disabled={isHistoryLoading} onClick={loadHistory}>
            Refresh
          </button>
        </div>

        {isHistoryLoading && <p>Loading history...</p>}

        {historyError && (
          <section className="message error-message" role="alert">
            {historyError}
          </section>
        )}

        {!isHistoryLoading &&
          !historyError &&
          history.length === 0 && <p>No summaries yet.</p>
        }

        <div className="history-list">
          {history.map((item) => (
            <article className="history-item" key={item.id}>
              <div className="history-date">
                {new Date(item.created_at).toLocaleString()}
              </div>

              <h3>Original text</h3>
              <p>{item.input}</p>

              <h3>Summary</h3>
              <p>{item.output}</p>
            </article>
          ))}
        </div>
      </section>
    </main>
  );
}

export default App;