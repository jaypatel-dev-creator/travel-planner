import { useState } from 'react';
import Header from './components/Layout/Header.jsx';
import TripForm from './components/Layout/TripForm.jsx';
import TripPage from './pages/TripPage.jsx';
import { useTrip } from './context/TripContext.jsx';

export default function App() {
  const { trip, trips, loading, error, loadTrips } = useTrip();
  const [creating, setCreating] = useState(false);

  const showForm = creating || (!loading && !error && trips.length === 0);

  return (
    <div className="app">
      <Header onNewTrip={() => setCreating(true)} />
      <main>
        {error && (
          <div className="banner error">
            <span>{error}</span>
            <button onClick={loadTrips}>Retry</button>
          </div>
        )}
        {loading ? (
          <p className="muted center">Loading trips…</p>
        ) : showForm ? (
          <TripForm
            onDone={() => setCreating(false)}
            onCancel={trips.length > 0 ? () => setCreating(false) : undefined}
          />
        ) : trip ? (
          <TripPage key={trip.id} />
        ) : null}
      </main>
    </div>
  );
}