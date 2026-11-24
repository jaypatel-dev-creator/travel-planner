import { useEffect } from 'react';
import { AdvancedMarker, APIProvider, Map, Pin, useMap } from '@vis.gl/react-google-maps';

const DEFAULT_CENTER = { lat: 20.5937, lng: 78.9629 }; // India
const DEFAULT_ZOOM = 4;

function MapController({ destinations, focusId }) {
  const map = useMap();
  // Re-fit only when the set of destinations changes, not on every trip update.
  const idsKey = destinations.map((d) => d.id).join(',');

  useEffect(() => {
    if (!map) return;
    if (destinations.length === 0) {
      map.setCenter(DEFAULT_CENTER);
      map.setZoom(DEFAULT_ZOOM);
    } else if (destinations.length === 1) {
      map.setCenter({ lat: destinations[0].lat, lng: destinations[0].lng });
      map.setZoom(13);
    } else {
      const bounds = new window.google.maps.LatLngBounds();
      destinations.forEach((d) => bounds.extend({ lat: d.lat, lng: d.lng }));
      map.fitBounds(bounds, 48);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [map, idsKey]);

  useEffect(() => {
    if (!map) return;
    const target = destinations.find((d) => d.id === focusId);
    if (target) {
      map.panTo({ lat: target.lat, lng: target.lng });
      map.setZoom(14);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [map, focusId]);

  return null;
}

export default function MapGoogle({ apiKey, destinations, focusId, onSelect }) {
  return (
    <APIProvider apiKey={apiKey}>
      <Map
        className="map"
        defaultCenter={DEFAULT_CENTER}
        defaultZoom={DEFAULT_ZOOM}
        mapId="DEMO_MAP_ID"
        gestureHandling="cooperative"
      >
        <MapController destinations={destinations} focusId={focusId} />
        {destinations.map((d) => (
          <AdvancedMarker
            key={d.id}
            position={{ lat: d.lat, lng: d.lng }}
            title={d.name}
            onClick={() => onSelect(d.id)}
          >
            <Pin background={d.id === focusId ? '#d93025' : '#1a73e8'} glyphColor="#ffffff" />
          </AdvancedMarker>
        ))}
      </Map>
    </APIProvider>
  );
}