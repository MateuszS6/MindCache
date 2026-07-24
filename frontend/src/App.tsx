import { useState } from "react";
import "./App.css";

type SummaryResponse = {
  summary: string;
};

const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

function App() {
  const [text, setText] = useState("");
  const [summary, setSummary] = useState("");
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);

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
    } catch (requestError) {
      console.error(requestError);
      setError(
        "The summary could not be generated. Check that the backend is running."
      );
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <main className="app">
      <section className="summary-card">
        <header className="page-header">
          <h1>Mind Cache</h1>
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
    </main>
  );
}

export default App;