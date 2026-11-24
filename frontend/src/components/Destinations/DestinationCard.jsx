import { useEffect, useState } from 'react';
import { useTrip } from '../../context/TripContext.jsx';

export default function DestinationCard({ destination, focused, onFocus }) {
  const { updateDestination, deleteDestination } = useTrip();
  const [notes, setNotes] = useState(destination.notes);
  const [error, setError] = useState('');
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    setNotes(destination.notes);
  }, [destination.notes]);

  const save = async () => {
    setError('');
    setSaving(true);
    try {
      await updateDestination(destination.id, { notes });
    } catch (e) {
      setError(e.message);
    } finally {
      setSaving(false);
    }
  };

  const remove = async () => {
    if (!window.confirm(`Remove "${destination.name}" from this trip?`)) return;
    setError('');
    try {
      await deleteDestination(destination.id);
    } catch (e) {
      setError(e.message);
    }
  };

  return (
    <article className={`dest-card ${focused ? 'focused' : ''}`}>
      <div className="dest-head">
        <button className="link dest-name" onClick={onFocus} title="Show on map">
          {destination.name}
        </button>
        <button className="link danger-text" onClick={remove}>
          Remove
        </button>
      </div>
      <p className="muted small">{destination.address}</p>
      <p className="rating">
        {destination.rating != null ? (
          <>
            <span className="star">★</span> {destination.rating}
            {destination.rating_count != null && (
              <span className="muted"> ({destination.rating_count.toLocaleString()} reviews)</span>
            )}
          </>
        ) : (
          <span className="muted">No rating available</span>
        )}
      </p>
      <label>
        Notes
        <textarea
          rows={2}
          maxLength={1000}
          value={notes}
          placeholder="Your notes about this place"
          onChange={(e) => setNotes(e.target.value)}
        />
      </label>
      {notes !== destination.notes && (
        <button className="primary small-btn" onClick={save} disabled={saving}>
          {saving ? 'Saving…' : 'Save notes'}
        </button>
      )}
      {error && <p className="error-text">{error}</p>}
    </article>
  );
}