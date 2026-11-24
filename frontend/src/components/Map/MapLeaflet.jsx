import { useEffect } from 'react';
import L from 'leaflet';
import { MapContainer, Marker, Popup, TileLayer, useMap } from 'react-leaflet';
import markerIcon from 'leaflet/dist/images/marker-icon.png';
import markerIcon2x from 'leaflet/dist/images/marker-icon-2x.png';
import markerShadow from 'leaflet/dist/images/marker-shadow.png';

// Leaflet's default marker icon paths break under bundlers; point them at the imported assets.
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconUrl: markerIcon,
  iconRetinaUrl: markerIcon2x,
  shadowUrl: markerShadow,
});

const DEFAULT_CENTER = [20.5937, 78.9629]; // India
const DEFAULT_ZOOM = 4;

function MapController({ destinations, focusId }) {
  const map = useMap();
  // Re-fit only when the set of destinations changes, not on every trip update.
  const idsKey = destinations.map((d) => d.id).join(',');

  useEffect(() => {
    if (destinations.length === 0) {
      map.setView(DEFAULT_CENTER, DEFAULT_ZOOM);
    } else if (destinations.length === 1) {
      map.setView([destinations[0].lat, destinations[0].lng], 13);
    } else {
      map.fitBounds(destinations.map((d) => [d.lat, d.lng]), { padding: [40, 40], maxZoom: 14 });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [map, idsKey]);

  useEffect(() => {
    const target = destinations.find((d) => d.id === focusId);
    if (target) map.flyTo([target.lat, target.lng], 14);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [map, focusId]);

  return null;
}

export default function MapLeaflet({ destinations, focusId, onSelect }) {
  return (
    <MapContainer className="map" center={DEFAULT_CENTER} zoom={DEFAULT_ZOOM} scrollWheelZoom>
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        url="https://tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      <MapController destinations={destinations} focusId={focusId} />
      {destinations.map((d) => (
        <Marker
          key={d.id}
          position={[d.lat, d.lng]}
          eventHandlers={{ click: () => onSelect(d.id) }}
        >
          <Popup>
            <strong>{d.name}</strong>
            <br />
            {d.address}
          </Popup>
        </Marker>
      ))}
    </MapContainer>
  );
}