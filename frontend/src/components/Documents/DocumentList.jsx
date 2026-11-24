import { useCallback, useEffect, useRef, useState } from 'react';
import { api } from '../../api/client';
import { useTrip } from '../../context/TripContext.jsx';
import { formatBytes } from '../../utils/format.js';

export default function DocumentList() {
  const { trip } = useTrip();
  const [docs, setDocs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState('');
  const inputRef = useRef(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      setDocs(await api.listDocuments(trip.id));
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, [trip.id]);

  useEffect(() => {
    load();
  }, [load]);

  const upload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setError('');
    setUploading(true);
    try {
      const created = await api.uploadDocument(trip.id, file);
      setDocs((prev) => [created, ...prev]);
    } catch (err) {
      setError(err.message);
    } finally {
      setUploading(false);
      if (inputRef.current) inputRef.current.value = '';
    }
  };

  const remove = async (doc) => {
    if (!window.confirm(`Delete "${doc.filename}"?`)) return;
    setError('');
    try {
      await api.deleteDocument(trip.id, doc.id);
      setDocs((prev) => prev.filter((d) => d.id !== doc.id));
    } catch (err) {
      setError(err.message);
    }
  };

  return (
    <section className="card">
      <h2>Travel documents</h2>
      <p className="muted small">Tickets, bookings, passport copies. PDF, PNG, JPG or TXT.</p>
      <input
        ref={inputRef}
        type="file"
        accept=".pdf,.png,.jpg,.jpeg,.txt"
        onChange={upload}
        disabled={uploading}
      />
      {uploading && <p className="muted">Uploading…</p>}
      {error && <p className="error-text">{error}</p>}

      {loading ? (
        <p className="muted">Loading documents…</p>
      ) : docs.length === 0 ? (
        <p className="muted">No documents yet.</p>
      ) : (
        <ul className="docs">
          {docs.map((d) => (
            <li key={d.id}>
              <a href={api.documentUrl(trip.id, d.id)} download={d.filename}>
                {d.filename}
              </a>
              <span className="muted small">{formatBytes(d.size_bytes)}</span>
              <button className="link danger-text" onClick={() => remove(d)}>
                Delete
              </button>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}