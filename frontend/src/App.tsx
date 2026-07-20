import { useState } from "react";
import "./App.css";

function App() {
  const [text, setText] = useState("");

  return (
    <main className="app">
      <section className="summary-card">
        <h1>Mind Cache</h1>
        <p>Turn long text into a clear summary.</p>

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

          <button type="button" disabled={!text.trim()}>
            Summarise
          </button>
        </div>
      </section>
    </main>
  );
}

export default App;