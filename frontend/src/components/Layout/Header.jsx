import { useState } from 'react';
import { useTrip } from '../../context/TripContext.jsx';
import { formatDate } from '../../utils/format.js';

export default function Header({ onNewTrip }) {
  const { trips, trip, selectedId, selectTrip, deleteTrip } = useTrip();
  const [error, setError] = useState('');

  const handleDelete = async () => {
    if (!trip || !window.confirm(`Delete "${trip.name}" and all its data?`)) return;
    setError('');
    try {
      await deleteTrip(trip.id);
    } catch (e) {
      setError(e.message);
    }
  };

  return (
    <header className="header">
      <h1>Travel Planner</h1>
      <div className="header-actions">
        {trips.length > 0 && (
          <select
            aria-label="Select trip"
            value={selectedId ?? ''}
            onChange={(e) => selectTrip(e.target.value)}
          >
            {trips.map((t) => (
              <option key={t.id} value={t.id}>
                {t.name} ({formatDate(t.start_date)})
              </option>
            ))}
          </select>
        )}
        <button className="primary" onClick={onNewTrip}>
          + New trip
        </button>
        {trip && (
          <button className="danger" onClick={handleDelete}>
            Delete trip
          </button>
        )}
      </div>
      {error && <span className="error-text">{error}</span>}
    </header>
  );
}