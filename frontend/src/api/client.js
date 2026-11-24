// Thin fetch wrapper. No business logic here: the server validates and calculates everything.
const BASE_URL = (import.meta.env.VITE_API_URL || 'http://localhost:8000').replace(/\/$/, '');

export class ApiError extends Error {
  constructor(message, status) {
    super(message);
    this.status = status;
  }
}

async function readError(res) {
  try {
    const body = await res.json();
    if (body?.message) return body.message; // our domain errors
    if (Array.isArray(body?.detail)) {
      // FastAPI/Pydantic validation errors
      return body.detail
        .map((d) => {
          const field = Array.isArray(d.loc) ? d.loc.slice(1).join('.') : '';
          return field ? `${field}: ${d.msg}` : d.msg;
        })
        .join('; ');
    }
  } catch {
    // body was not JSON
  }
  return `Request failed (${res.status}).`;
}

async function request(path, { method = 'GET', json, formData } = {}) {
  let res;
  try {
    res = await fetch(`${BASE_URL}${path}`, {
      method,
      headers: json !== undefined ? { 'Content-Type': 'application/json' } : undefined,
      body: formData ?? (json !== undefined ? JSON.stringify(json) : undefined),
    });
  } catch {
    throw new ApiError('Cannot reach the server. Is the backend running?', 0);
  }
  if (!res.ok) throw new ApiError(await readError(res), res.status);
  if (res.status === 204) return null;
  return res.json();
}

export const api = {
  // Trips
  listTrips: () => request('/trips'),
  createTrip: (payload) => request('/trips', { method: 'POST', json: payload }),
  updateTrip: (id, payload) => request(`/trips/${id}`, { method: 'PATCH', json: payload }),
  deleteTrip: (id) => request(`/trips/${id}`, { method: 'DELETE' }),

  // Destinations
  addDestination: (tripId, payload) =>
    request(`/trips/${tripId}/destinations`, { method: 'POST', json: payload }),
  updateDestination: (tripId, destId, payload) =>
    request(`/trips/${tripId}/destinations/${destId}`, { method: 'PATCH', json: payload }),
  deleteDestination: (tripId, destId) =>
    request(`/trips/${tripId}/destinations/${destId}`, { method: 'DELETE' }),

  // Activities
  addActivity: (tripId, payload) =>
    request(`/trips/${tripId}/activities`, { method: 'POST', json: payload }),
  updateActivity: (tripId, activityId, payload) =>
    request(`/trips/${tripId}/activities/${activityId}`, { method: 'PATCH', json: payload }),
  deleteActivity: (tripId, activityId) =>
    request(`/trips/${tripId}/activities/${activityId}`, { method: 'DELETE' }),

  // Places
  searchPlaces: (q) => request(`/places/search?q=${encodeURIComponent(q)}`),

  // Documents
  listDocuments: (tripId) => request(`/trips/${tripId}/documents`),
  uploadDocument: (tripId, file) => {
    const formData = new FormData();
    formData.append('file', file);
    return request(`/trips/${tripId}/documents`, { method: 'POST', formData });
  },
  deleteDocument: (tripId, docId) =>
    request(`/trips/${tripId}/documents/${docId}`, { method: 'DELETE' }),
  documentUrl: (tripId, docId) => `${BASE_URL}/trips/${tripId}/documents/${docId}`,

  // Assistant
  generateItinerary: (tripId, payload) =>
    request(`/trips/${tripId}/assistant/itinerary`, { method: 'POST', json: payload }),
  chat: (tripId, payload) =>
    request(`/trips/${tripId}/assistant/chat`, { method: 'POST', json: payload }),
};