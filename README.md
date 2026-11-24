# Travel Planner

Trip-planning app: define destinations, build a day-by-day itinerary, track a trip budget, and store travel documents.

**Stack:** FastAPI (Python) · MongoDB (PyMongo Async) · React + Vite · Google Maps/Places with an OpenStreetMap fallback · Gemini assistant.

All business logic, validation and calculations live on the server. The frontend only presents data and handles interaction.

## Features

- **Interactive map** pinning every destination (Google Maps with a key, Leaflet + OpenStreetMap without).
- **Itinerary timeline**: vertical, chronological, grouped by day.
- **Destination cards**: place info, rating, and your own notes.
- **Budget vs Actual**: estimated cost per activity, optional actual cost, and a Trip Budget progress bar at the top. Every figure is calculated by the backend.
- **Travel documents**: upload, download and delete tickets and bookings per trip (PDF, PNG, JPG, TXT).
- **Extra feature 1, AI itinerary generator**: describe the trip in a sentence and Gemini drafts activities. The server validates each one (dates inside the trip, costs, times) before saving it.
- **Extra feature 2, budget-aware chat**: ask "what can I cut?" and the assistant answers from your real activities and the server-computed budget.

## Known limitations

1. **OpenStreetMap has no ratings.** Google Places returns a rating and review count. With no Google key, place search uses OpenStreetMap and `rating` is `null`; cards show "No rating available".
2. **Google keys are optional.** Google now requires MFA to create keys, so the app runs with none: place search falls back to OpenStreetMap and the map to Leaflet. With `GOOGLE_PLACES_API_KEY` (server) and `VITE_GOOGLE_MAPS_API_KEY` (browser) set, Google is used instead. The Google path was not exercised in development.
3. **The assistant needs a Gemini key** (`GOOGLE_API_KEY`). Without it the assistant returns a "not configured" message and everything else works.
4. **No authentication.** Trips are not tied to users.
5. **No automated tests.**

## Architecture

```
backend/app/
  api/routes/     HTTP layer only (trips, places, documents, assistant, health)
  services/       Business logic (trip, budget, places, document, assistant)
  schemas/        Pydantic request/response models and validation
  core/           Config, logging, domain exceptions
  db/             MongoDB connection and indexes

frontend/src/
  api/            Fetch wrapper for every endpoint
  context/        TripContext: one source of truth for trips
  components/     Budget, Timeline, Map, Destinations, Documents, Assistant, Layout
  pages/          TripPage (composes the components)
```

- **Budget:** `budget_service.compute_budget` is a pure function using `Decimal`, so currency sums don't drift. Every trip mutation returns the full trip with the recomputed budget, and the frontend just displays it.
- **Budget status:** `on_track` below 80% of budget, `near_limit` from 80%, `over_budget` above 100%, `no_budget` when the budget is 0.
- **Storage:** one MongoDB document per trip with nested `destinations` and `activities` arrays. Documents are stored in GridFS.
- **Place ids:** Google ids are stored as-is; OpenStreetMap ids are stored as `osm:<type>:<id>` so they never collide.
- **OSM etiquette:** requests are spaced at least 1 second apart with an identifying User-Agent, and search runs on a button press, not on every keystroke.
- **AI output is untrusted:** generated activities go through the same validation path as manual ones, and invalid ones are skipped.

## API

| Method | Path |
|---|---|
| POST / GET | `/trips` |
| GET / PATCH / DELETE | `/trips/{trip_id}` |
| GET | `/trips/{trip_id}/budget` |
| POST | `/trips/{trip_id}/destinations` |
| PATCH / DELETE | `/trips/{trip_id}/destinations/{destination_id}` |
| POST | `/trips/{trip_id}/activities` |
| PATCH / DELETE | `/trips/{trip_id}/activities/{activity_id}` |
| POST / GET | `/trips/{trip_id}/documents` |
| GET / DELETE | `/trips/{trip_id}/documents/{document_id}` |
| POST | `/trips/{trip_id}/assistant/itinerary` |
| POST | `/trips/{trip_id}/assistant/chat` |
| GET | `/places/search?q=...` |

Interactive docs at `/docs` when `APP_ENV=development`.

## Run it

**Backend** (Python 3.11+, a running MongoDB):

```bash
cd backend
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env             # then edit .env
uvicorn app.main:app --reload
```

Minimum `.env`: `MONGODB_URI`. Leave the Google keys empty to use OpenStreetMap. Set `GOOGLE_API_KEY` to enable the assistant, and `GEMINI_MODEL` if you want a different model.

**Frontend** (Node 20.19+ or 22.12+):

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

Open http://localhost:5173. The backend must run on the URL in `VITE_API_URL` (default `http://localhost:8000`).

Never commit `.env` files. If you set `VITE_GOOGLE_MAPS_API_KEY`, restrict that key by HTTP referrer in Google Cloud, because browser keys are visible to users.