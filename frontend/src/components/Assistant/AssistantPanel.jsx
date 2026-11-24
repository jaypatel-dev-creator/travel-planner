import { useRef, useState } from 'react';
import { api } from '../../api/client';
import { useTrip } from '../../context/TripContext.jsx';

const SUGGESTIONS = ['Am I on track with my budget?', 'What can I cut to save money?'];

export default function AssistantPanel() {
  const { trip, applyTrip } = useTrip();
  const [tab, setTab] = useState('itinerary');

  // Itinerary generator
  const [prompt, setPrompt] = useState('');
  const [generating, setGenerating] = useState(false);
  const [genResult, setGenResult] = useState('');
  const [genError, setGenError] = useState('');

  // Budget chat
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [thinking, setThinking] = useState(false);
  const [chatError, setChatError] = useState('');
  const listRef = useRef(null);

  const generate = async (e) => {
    e.preventDefault();
    setGenError('');
    setGenResult('');
    setGenerating(true);
    try {
      const result = await api.generateItinerary(trip.id, { prompt: prompt.trim() });
      applyTrip(result.trip);
      setGenResult(
        `Added ${result.added} activit${result.added === 1 ? 'y' : 'ies'}` +
          (result.skipped ? `, skipped ${result.skipped} that did not fit the trip.` : '.')
      );
      setPrompt('');
    } catch (err) {
      setGenError(err.message);
    } finally {
      setGenerating(false);
    }
  };

  const send = async (text) => {
    const message = text.trim();
    if (!message || thinking) return;
    setChatError('');
    setThinking(true);
    const history = messages.slice(-10);
    setMessages((m) => [...m, { role: 'user', content: message }]);
    setInput('');
    try {
      const { reply } = await api.chat(trip.id, { message, history });
      setMessages((m) => [...m, { role: 'assistant', content: reply }]);
    } catch (err) {
      setChatError(err.message);
    } finally {
      setThinking(false);
      setTimeout(() => listRef.current?.scrollTo({ top: listRef.current.scrollHeight }), 0);
    }
  };

  return (
    <section className="card">
      <h2>AI assistant</h2>
      <div className="tabs" role="tablist">
        <button role="tab" aria-selected={tab === 'itinerary'} className={tab === 'itinerary' ? 'active' : ''} onClick={() => setTab('itinerary')}>
          Generate itinerary
        </button>
        <button role="tab" aria-selected={tab === 'chat'} className={tab === 'chat' ? 'active' : ''} onClick={() => setTab('chat')}>
          Budget chat
        </button>
      </div>

      {tab === 'itinerary' ? (
        <form className="form-grid" onSubmit={generate}>
          <label>
            Describe what you want
            <textarea
              rows={3}
              maxLength={500}
              required
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              placeholder="Relaxed 3 days with beaches, local food and one day of sightseeing"
            />
          </label>
          <p className="muted small">
            Activities are added to this trip within its dates and checked by the server like any manual entry.
          </p>
          {genError && <p className="error-text">{genError}</p>}
          {genResult && <p className="success-text">{genResult}</p>}
          <button className="primary" disabled={generating || prompt.trim().length < 3}>
            {generating ? 'Generating…' : 'Generate activities'}
          </button>
        </form>
      ) : (
        <div className="chat">
          <div className="chat-list" ref={listRef}>
            {messages.length === 0 && (
              <div className="suggestions">
                {SUGGESTIONS.map((s) => (
                  <button key={s} onClick={() => send(s)}>
                    {s}
                  </button>
                ))}
              </div>
            )}
            {messages.map((m, i) => (
              <div key={i} className={`bubble ${m.role}`}>
                {m.content}
              </div>
            ))}
            {thinking && <div className="bubble assistant muted">Thinking…</div>}
          </div>
          {chatError && <p className="error-text">{chatError}</p>}
          <form
            className="inline-form"
            onSubmit={(e) => {
              e.preventDefault();
              send(input);
            }}
          >
            <input
              value={input}
              maxLength={1000}
              placeholder="Ask about your budget or plan"
              onChange={(e) => setInput(e.target.value)}
            />
            <button className="primary" disabled={thinking || !input.trim()}>
              Send
            </button>
          </form>
        </div>
      )}
    </section>
  );
}