import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import { api } from '../api/client';

const TripContext = createContext(null);
const STORAGE_KEY = 'travel-planner:selected-trip';

function readStoredId() {
  try {
    return localStorage.getItem(STORAGE_KEY);
  } catch {
    return null;
  }
}

function storeId(id) {
  try {
    if (id) localStorage.setItem(STORAGE_KEY, id);
    else localStorage.removeItem(STORAGE_KEY);
  } catch {
    // storage unavailable: selection just won't persist
  }
}

export function TripProvider({ children }) {
  const [trips, setTrips] = useState([]);
  const [selectedId, setSelectedId] = useState(readStoredId);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const trip = useMemo(() => trips.find((t) => t.id === selectedId) ?? null, [trips, selectedId]);

  const loadTrips = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const list = await api.listTrips();
      setTrips(list);
      setSelectedId((current) =>
        list.some((t) => t.id === current) ? current : (list[0]?.id ?? null)
      );
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadTrips();
  }, [loadTrips]);

  useEffect(() => {
    storeId(selectedId);
  }, [selectedId]);

  // Every mutation endpoint returns the full trip (budget included): replace it in place.
  const applyTrip = useCallback((updated) => {
    setTrips((prev) =>
      prev.some((t) => t.id === updated.id)
        ? prev.map((t) => (t.id === updated.id ? updated : t))
        : [updated, ...prev]
    );
  }, []);

  const mutate = async (call) => {
    const updated = await call();
    applyTrip(updated);
    return updated;
  };

  const value = {
    trips,
    trip,
    selectedId,
    loading,
    error,
    loadTrips,
    applyTrip,
    selectTrip: setSelectedId,

    createTrip: async (payload) => {
      const created = await api.createTrip(payload);
      applyTrip(created);
      setSelectedId(created.id);
      return created;
    },
    updateTrip: (payload) => mutate(() => api.updateTrip(trip.id, payload)),
    deleteTrip: async (id) => {
      await api.deleteTrip(id);
      const next = trips.filter((t) => t.id !== id);
      setTrips(next);
      if (selectedId === id) setSelectedId(next[0]?.id ?? null);
    },

    addDestination: (payload) => mutate(() => api.addDestination(trip.id, payload)),
    updateDestination: (destId, payload) =>
      mutate(() => api.updateDestination(trip.id, destId, payload)),
    deleteDestination: (destId) => mutate(() => api.deleteDestination(trip.id, destId)),

    addActivity: (payload) => mutate(() => api.addActivity(trip.id, payload)),
    updateActivity: (activityId, payload) =>
      mutate(() => api.updateActivity(trip.id, activityId, payload)),
    deleteActivity: (activityId) => mutate(() => api.deleteActivity(trip.id, activityId)),
  };

  return <TripContext.Provider value={value}>{children}</TripContext.Provider>;
}

export function useTrip() {
  const ctx = useContext(TripContext);
  if (!ctx) throw new Error('useTrip must be used inside <TripProvider>.');
  return ctx;
}