# Travio AI: Setup & Operations Guide (Milestones 1-3 & Duffel Travel API)

This guide documents the setup, environment configuration, database migrations, testing, and execution of **Travio AI**.

---

## 1. Architecture Stack Summary

- **Backend**: Python 3.10+, FastAPI (modular monolith), SQLAlchemy 2.0 (async), Alembic, Pydantic v2, PyJWT, HTTPX.
- **Frontend**: React Native, Expo SDK 58, Expo Router, JavaScript & JSX exclusively.
- **Authentication**: Supabase Auth (JWT Bearer tokens verified on FastAPI).
- **Travel API Provider**: Duffel API (`https://duffel.com/docs`) for flights (`/air/offer_requests`) and accommodations (`/stays/search`).
- **Database**: PostgreSQL (with in-memory async SQLite fixtures for isolated test suites).

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

All 44 tests execute in an isolated in-memory test database with zero external network dependencies:
```
tests/integration/test_auth_and_trips.py::test_unauthenticated_profile_access_returns_401 PASSED
tests/integration/test_auth_and_trips.py::test_get_and_sync_profile PASSED
tests/integration/test_auth_and_trips.py::test_trip_crud_and_ownership PASSED
tests/integration/test_auth_and_trips.py::test_cross_user_access_rejection_idor PASSED
tests/integration/test_auth_and_trips.py::test_role_hierarchy_permissions PASSED
tests/integration/test_auth_and_trips.py::test_input_validation_rules PASSED
tests/integration/test_health_api.py::test_health_endpoint_returns_200 PASSED
tests/integration/test_health_api.py::test_root_endpoint PASSED
tests/integration/test_health_api.py::test_unknown_endpoint_returns_404 PASSED
tests/integration/test_health_api.py::test_cors_headers_allowed PASSED
tests/integration/test_itinerary_and_places.py::test_places_creation_and_coordinate_validation PASSED
tests/integration/test_itinerary_and_places.py::test_itinerary_days_crud_and_date_validation PASSED
tests/integration/test_itinerary_and_places.py::test_itinerary_activities_crud_and_schedule_validation PASSED
tests/integration/test_itinerary_and_places.py::test_reorder_transaction_rollback_on_failure PASSED
tests/integration/test_itinerary_and_places.py::test_itinerary_authorization_and_cross_user_rejection PASSED
tests/integration/test_travel_offers_api.py::test_flight_search_api_success PASSED
tests/integration/test_travel_offers_api.py::test_hotel_search_api_success PASSED
tests/integration/test_travel_offers_api.py::test_flight_search_with_trip_persistence PASSED
tests/integration/test_travel_offers_api.py::test_get_stored_travel_offer_and_expiration_detection PASSED
tests/integration/test_travel_offers_api.py::test_offers_api_provider_unavailable_503 PASSED
tests/unit/test_database.py::test_successful_database_connection PASSED
tests/unit/test_database.py::test_failed_database_connection PASSED
tests/unit/test_database.py::test_get_db_session_lifecycle_and_rollback PASSED
tests/unit/test_database.py::test_guid_type_decorator PASSED
tests/unit/test_duffel_adapter.py::test_adapter_initialization_and_headers PASSED
tests/unit/test_duffel_adapter.py::test_flight_search_builds_payload_correctly PASSED
tests/unit/test_duffel_adapter.py::test_flight_search_normalizes_duffel_response PASSED
tests/unit/test_duffel_adapter.py::test_flight_search_handles_malformed_slices PASSED
tests/unit/test_duffel_adapter.py::test_hotel_search_builds_payload_correctly PASSED
tests/unit/test_duffel_adapter.py::test_hotel_search_normalizes_duffel_response PASSED
tests/unit/test_duffel_adapter.py::test_hotel_search_handles_missing_rates PASSED
tests/unit/test_duffel_adapter.py::test_adapter_raises_auth_error_on_401 PASSED
tests/unit/test_duffel_adapter.py::test_adapter_raises_rate_limit_error_on_429 PASSED
tests/unit/test_duffel_adapter.py::test_adapter_raises_service_unavailable_on_500 PASSED
tests/unit/test_duffel_adapter.py::test_adapter_raises_service_unavailable_on_timeout PASSED
tests/unit/test_duffel_adapter.py::test_empty_offers_returns_empty_list PASSED
tests/unit/test_duffel_adapter.py::test_iso_duration_parsing PASSED
tests/unit/test_security.py::test_verify_valid_token PASSED
tests/unit/test_security.py::test_verify_expired_token PASSED
tests/unit/test_security.py::test_verify_invalid_signature PASSED
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

## 7. Testing Travel Offers (Duffel API Endpoints)

The travel offers endpoints are accessible at `/api/v1/offers/*`:

### Flight Search: `POST /api/v1/offers/flights/search`
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

### Hotel / Accommodation Search: `POST /api/v1/offers/hotels/search`
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

### Retrieve Stored Offer & Check Expiration: `GET /api/v1/offers/{offer_id}`
Returns the normalized offer details alongside `is_expired: true/false`.

> **Data Integrity Guarantee**: All returned prices correspond strictly to live Duffel quotes with explicit currency, expiration timestamp, and offer IDs. Offers are never fabricated. If Duffel is unreachable or invalid credentials are supplied, the API responds with HTTP 503 (or HTTP 500 configuration notice) rather than mock/fake prices.
