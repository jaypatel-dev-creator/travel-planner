import { useState } from 'react';
import { api } from '../../api/client';
import { useTrip } from '../../context/TripContext.jsx';

export default function PlaceSearch() {
  const { trip, addDestination } = useTrip();
  const [query, setQuery] = useState('');
  const [results, setResults] = useState(null);
  const [searching, setSearching] = useState(false);
  const [error, setError] = useState('');

  const added = new Set(trip.destinations.map((d) => d.place_id));

  // Explicit search button (not search-as-you-type): keeps us within Nominatim's usage policy.
  const search = async (e) => {
    e.preventDefault();
    const q = query.trim();
    if (q.length < 2) return;
    setError('');
    setSearching(true);
    try {
      const data = await api.searchPlaces(q);
      setResults(data.results);
    } catch (err) {
      setError(err.message);
      setResults(null);
    } finally {
      setSearching(false);
    }
  };

  const add = async (place) => {
    setError('');
    try {
      await addDestination({ place, notes: '' });
    } catch (err) {
      setError(err.message);
    }
  };

  return (
    <div className="place-search">
      <form className="inline-form" onSubmit={search}>
        <input
          value={query}
          maxLength={100}
          placeholder="Search a place, e.g. Gateway of India"
          onChange={(e) => setQuery(e.target.value)}
        />
        <button className="primary" disabled={searching || query.trim().length < 2}>
          {searching ? 'Searching…' : 'Search'}
        </button>
      </form>
      {error && <p className="error-text">{error}</p>}

      {results && (
        <>
          {results.length === 0 ? (
            <p className="muted">No places found. Try a more specific name.</p>
          ) : (
            <ul className="results">
              {results.map((p) => (
                <li key={p.place_id}>
                  <div>
                    <strong>{p.name}</strong>
                    <div className="muted small">{p.address}</div>
                  </div>
                  {added.has(p.place_id) ? (
                    <span className="muted small">Added</span>
                  ) : (
                    <button onClick={() => add(p)}>Add</button>
                  )}
                </li>
              ))}
            </ul>
          )}
          {results.length > 0 && results.every((p) => p.rating == null) && (
            <p className="muted small">Ratings come from Google Places and are not available for OpenStreetMap results.</p>
          )}
        </>
      )}
    </div>
  );
}