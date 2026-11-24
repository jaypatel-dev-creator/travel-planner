import { lazy, Suspense } from 'react';

// Google Maps when a browser key is configured, otherwise Leaflet + OpenStreetMap tiles.
// Both are lazy-loaded so only the one in use is downloaded.
const GOOGLE_KEY = import.meta.env.VITE_GOOGLE_MAPS_API_KEY;
const MapGoogle = lazy(() => import('./MapGoogle.jsx'));
const MapLeaflet = lazy(() => import('./MapLeaflet.jsx'));

export default function TripMap({ destinations, focusId, onSelect }) {
  return (
    <div className="map-wrap">
      <Suspense fallback={<div className="map-loading">Loading map…</div>}>
        {GOOGLE_KEY ? (
          <MapGoogle apiKey={GOOGLE_KEY} destinations={destinations} focusId={focusId} onSelect={onSelect} />
        ) : (
          <MapLeaflet destinations={destinations} focusId={focusId} onSelect={onSelect} />
        )}
      </Suspense>
      {destinations.length === 0 && <p className="muted small">Add a destination to pin it on the map.</p>}
    </div>
  );
}