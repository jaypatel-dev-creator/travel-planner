import { useState } from 'react';
import BudgetBar from '../components/Budget/BudgetBar.jsx';
import Timeline from '../components/Timeline/Timeline.jsx';
import TripMap from '../components/Map/TripMap.jsx';
import PlaceSearch from '../components/Destinations/PlaceSearch.jsx';
import DestinationCard from '../components/Destinations/DestinationCard.jsx';
import DocumentList from '../components/Documents/DocumentList.jsx';
import AssistantPanel from '../components/Assistant/AssistantPanel.jsx';
import { useTrip } from '../context/TripContext.jsx';
import { formatDate } from '../utils/format.js';

export default function TripPage() {
  const { trip } = useTrip();
  const [focusId, setFocusId] = useState(null);

  return (
    <>
      <BudgetBar />
      <div className="trip-title">
        <h2>{trip.name}</h2>
        <span className="muted">
          {formatDate(trip.start_date)} to {formatDate(trip.end_date)}
        </span>
      </div>

      <div className="layout">
        <div className="col">
          <Timeline />
        </div>

        <div className="col">
          <section className="card">
            <h2>Map</h2>
            <TripMap destinations={trip.destinations} focusId={focusId} onSelect={setFocusId} />
          </section>

          <section className="card">
            <h2>Destinations</h2>
            <PlaceSearch />
            {trip.destinations.length === 0 ? (
              <p className="muted">No destinations yet. Search for a place above and add it.</p>
            ) : (
              <div className="cards">
                {trip.destinations.map((d) => (
                  <DestinationCard
                    key={d.id}
                    destination={d}
                    focused={d.id === focusId}
                    onFocus={() => setFocusId(d.id)}
                  />
                ))}
              </div>
            )}
          </section>

          <AssistantPanel />
          <DocumentList />
        </div>
      </div>
    </>
  );
}