# Travio AI: Setup & Operations Guide (Milestones 1-4: Places, Routing, Weather, Offers)

This guide documents the setup, environment configuration, database migrations, testing, and execution of **Travio AI**.

---

## 1. Architecture Stack Summary

- **Backend**: Python 3.10+, FastAPI (modular monolith), SQLAlchemy 2.0 (async), Alembic, Pydantic v2, PyJWT, HTTPX.
- **Frontend**: React Native, Expo SDK 58, Expo Router, JavaScript & JSX exclusively.
- **Authentication**: Supabase Auth (JWT Bearer tokens verified on FastAPI via asymmetric JWKS / ES256).
- **Places & Geocoding**: Geoapify Places API (`https://api.geoapify.com`)
- **Routing Engine**: OSRM (Open Source Routing Machine API, pluggable behind `RoutingAdapterInterface`)
- **Weather Forecasts**: Open-Meteo API (`https://api.open-meteo.com`)
- **Travel API Provider**: Duffel API (`https://duffel.com/docs`) for flights (`/air/offer_requests`) and accommodations (`/stays/search`).
- **Database**: PostgreSQL / SQLite (with in-memory async SQLite fixtures for isolated test suites).

---

## 2. Environment Variables Configuration

### Backend (`backend/.env`)
Create a `.env` file in `backend/` copied from `.env.example`:
```env
ENVIRONMENT=development
PROJECT_NAME="Travio AI Backend"
API_V1_PREFIX=/api/v1
CORS_ORIGINS=["http://localhost:8081","http://localhost:19006","http://localhost:3000","*"]

# Supabase Auth Configuration
SUPABASE_URL=https://<your-project-ref>.supabase.co
SUPABASE_JWT_SECRET=<your-supabase-jwt-secret>
SUPABASE_AUDIENCE=authenticated

# PostgreSQL Database (Asyncpg Driver)
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/travio_db
DATABASE_ECHO=false

# Duffel Travel API Configuration
DUFFEL_ACCESS_TOKEN=your-duffel-access-token
DUFFEL_API_URL=https://api.duffel.com
DUFFEL_VERSION=v2

# Places & Geocoding Provider
GEOAPIFY_API_KEY=216dda85c29e41069d958bb97d9dd40c
```

#### Obtaining a Duffel Access Token
1. Register for an account at [Duffel Dashboard](https://app.duffel.com/).
2. Navigate to **Developer > Access Tokens**.
3. Create a **Test Token** (prefixed with `duffel_test_`). Test tokens allow querying live test data and simulation modes without incurring charges.
4. Paste the token into `DUFFEL_ACCESS_TOKEN`.
> **Note**: Automated unit and integration tests use HTTP mock transports and do NOT require live Duffel API credentials. Live flight and hotel searches against Duffel require a valid `DUFFEL_ACCESS_TOKEN`.

### Mobile Frontend (`mobile/.env`)
Create a `.env` file in `mobile/` copied from `.env.example`:
```env
# Optional: Explicit backend URL override (e.g., http://192.168.1.10:8000 for physical phone)
# If omitted, Expo auto-detects hostUri or defaults to 10.0.2.2 (Android Emulator) / localhost (Web)
EXPO_PUBLIC_API_URL=

# Supabase Public Keys
EXPO_PUBLIC_SUPABASE_URL=https://<your-project-ref>.supabase.co
EXPO_PUBLIC_SUPABASE_ANON_KEY=<your-supabase-anon-key>
```
> **Security Note**: Never put the Supabase service-role secret, database passwords, or provider API keys into mobile `EXPO_PUBLIC_*` variables. Only the public anon key is safe on the client. External travel API requests go through the FastAPI backend.

---

## 3. PostgreSQL Database Setup & Migrations

### Local PostgreSQL Database Creation
Ensure PostgreSQL is running locally:
```sql
CREATE DATABASE travio_db;
```

### Alembic Migration Commands
To apply migrations against your configured PostgreSQL database:
```powershell
cd d:\nnaik\Travio-Project\backend
.\.venv\Scripts\Activate.ps1

# Upgrade database to latest revision
alembic upgrade head

# Rollback last migration if needed
alembic downgrade -1
```

Migration scripts:
- `001_initial_milestone2.py`: sets up `profiles`, `trips`, and `trip_members`.
- `002_milestone3_itinerary.py`: sets up `places`, `itinerary_days`, and `itinerary_items` with unique constraints `(trip_id, day_number)` and `(day_id, order_index)` and cascade foreign keys.
- `003_duffel_travel_offers.py`: sets up `search_records` and `travel_offers` for persistent flight and hotel search queries and verified offers.

---

## 4. Running Backend Automated Tests

Run the complete test suite (unit tests for JWT security, database lifecycle, Duffel adapter serialization & error handling + integration tests for profiles, trips, itinerary days, activities, places, and Duffel travel offers):
```powershell
cd d:\nnaik\Travio-Project\backend
.\.venv\Scripts\Activate.ps1
pytest -v
```

All 60 tests execute in an isolated in-memory test database with zero external network dependencies:
```
backend/tests/integration/test_auth_and_trips.py (6 tests) ............ PASSED
backend/tests/integration/test_health_api.py (4 tests) ................ PASSED
backend/tests/integration/test_itinerary_and_places.py (5 tests) ...... PASSED
backend/tests/integration/test_places_routing_weather_api.py (4 tests)  PASSED
backend/tests/integration/test_travel_offers_api.py (5 tests) ......... PASSED
backend/tests/unit/test_database.py (4 tests) ......................... PASSED
backend/tests/unit/test_duffel_adapter.py (13 tests) .................. PASSED
backend/tests/unit/test_geoapify_adapter.py (4 tests) ................. PASSED
backend/tests/unit/test_openmeteo_adapter.py (4 tests) ................ PASSED
backend/tests/unit/test_osrm_adapter.py (4 tests) ..................... PASSED
backend/tests/unit/test_security.py (7 tests) ......................... PASSED

============================= 60 passed ==============================
```
tests/unit/test_security.py::test_verify_invalid_audience PASSED
tests/unit/test_security.py::test_verify_malformed_token PASSED
tests/unit/test_security.py::test_verify_missing_token PASSED
tests/unit/test_security.py::test_verify_invalid_uuid_subject PASSED
```

---

## 5. Starting the Applications

### Starting the FastAPI Backend
```powershell
cd d:\nnaik\Travio-Project\backend
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
- Interactive Swagger API docs: `http://localhost:8000/api/v1/docs`
- Health check: `http://localhost:8000/api/v1/health`

### Starting the Mobile Application
```powershell
cd d:\nnaik\Travio-Project\mobile
npm start
```

---

## 6. How to Test on Mobile (Web, Android Emulator, Physical Device)

1. **Web**: Press `w` in the Expo terminal. Opens in browser at `http://localhost:8081`.
2. **Android Emulator**: Start an Android Virtual Device in Android Studio, then press `a` in the Expo terminal.
3. **Physical Android Phone**: Open Expo Go, scan the terminal QR code. Ensure your phone is on the same local Wi-Fi.

### Testing Auth and Trip Creation Flow:
1. Tap **Sign In / Register** on the home screen.
2. If testing registration, navigate to **Register** and submit full name, email, and password.
3. Once logged in, the top banner displays your verified profile avatar and email.
4. Tap **+ New Trip**, fill in title, destination, dates, and budget, and submit.
5. The trip is persisted to the database and appears in **My Trips** with an **OWNER** badge.
6. Test deleting the trip or viewing diagnostic network latency on the live health card.

### Testing Milestone 3 Itinerary & Interactive Map Flow:
1. Tap **📅 Itinerary & Map →** on any trip card.
2. The **Trip Details Screen** displays the trip metadata and list of scheduled days.
3. Tap **+ Add Day**, enter Day 1 with a valid date within the trip boundaries, and submit.
4. Tap **View Itinerary →** on the day card to open the **Day-wise Itinerary Screen**.
5. Tap **+ Add Activity**, fill in the activity name (e.g., "Sensō-ji Temple"), start/end times (e.g., `09:00:00` - `11:30:00`), venue name, and geographical coordinates (e.g. `35.7148`, `139.7967`), then save.
6. Test deterministic validation: try adding another activity overlapping that time window or with `end_time <= start_time` to observe deterministic rejection.
7. Tap **▲ Up** or **▼ Down** to verify atomic chronological activity reordering.
8. Tap **🗺️ View on Map** to open the **Interactive Map Screen**:
   - On **Android Emulator / Device**: `react-native-maps` renders native map pins (`#1`, `#2`) with callouts and sequential order badges. Tapping any activity in the carousel smoothly pans the map to that pin.
   - On **Web**: The graceful Geo-Route Inspector displays the ordered stops, location badges, and direct external maps link without crashing.

---

## 7. Testing Milestone 4 Provider APIs (Places, Routes, Weather & Offers)

### A. Places & POIs Search (Geoapify): `GET /api/v1/places/search`
```bash
curl -X GET "http://localhost:8000/api/v1/places/search?text=Paris&categories=tourism.attraction&limit=5" \
  -H "Authorization: Bearer <your-supabase-jwt>"
```

### B. Routing Calculation (OSRM): `POST /api/v1/routes/calculate`
```bash
curl -X POST "http://localhost:8000/api/v1/routes/calculate" \
  -H "Authorization: Bearer <your-supabase-jwt>" \
  -H "Content-Type: application/json" \
  -d '{
    "origin": { "latitude": 48.8566, "longitude": 2.3522 },
    "destination": { "latitude": 48.8584, "longitude": 2.2945 },
    "profile": "driving"
  }'
```

### C. Live Weather Forecast (Open-Meteo): `GET /api/v1/weather/forecast`
```bash
curl -X GET "http://localhost:8000/api/v1/weather/forecast?lat=48.8566&lon=2.3522&days=7" \
  -H "Authorization: Bearer <your-supabase-jwt>"
```

### D. Flight Search (Duffel API): `POST /api/v1/offers/flights/search`
```bash
curl -X POST "http://localhost:8000/api/v1/offers/flights/search" \
  -H "Authorization: Bearer <your-supabase-jwt>" \
  -H "Content-Type: application/json" \
  -d '{
    "origin": "JFK",
    "destination": "LHR",
    "departure_date": "2026-12-01",
    "return_date": "2026-12-10",
    "adults": 1,
    "cabin_class": "economy"
  }'
```

### E. Hotel / Accommodation Search (Duffel Stays): `POST /api/v1/offers/hotels/search`
```bash
curl -X POST "http://localhost:8000/api/v1/offers/hotels/search" \
  -H "Authorization: Bearer <your-supabase-jwt>" \
  -H "Content-Type: application/json" \
  -d '{
    "latitude": 40.7580,
    "longitude": -73.9855,
    "radius_km": 5,
    "check_in_date": "2026-12-01",
    "check_out_date": "2026-12-05",
    "rooms": 1,
    "guests": 2
  }'
```

### F. Retrieve Stored Offer & Check Expiration: `GET /api/v1/offers/{offer_id}`
Returns the normalized offer details alongside `is_expired: true/false`.

> **Data Integrity Guarantee**: All returned prices correspond strictly to live Duffel quotes with explicit currency, expiration timestamp, and offer IDs. Offers and weather are never fabricated. If providers are unreachable, the API responds with HTTP 503 rather than mock/fake prices.
