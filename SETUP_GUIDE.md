# Travio AI: Setup & Operations Guide (Milestones 1 & 2)

This guide documents the setup, environment configuration, database migrations, testing, and execution of **Travio AI**.

---

## 1. Architecture Stack Summary

- **Backend**: Python 3.10+, FastAPI (modular monolith), SQLAlchemy 2.0 (async), Alembic, Pydantic v2, PyJWT.
- **Frontend**: React Native, Expo SDK 58, Expo Router, JavaScript & JSX exclusively.
- **Authentication**: Supabase Auth (JWT Bearer tokens verified on FastAPI).
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
```

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
> **Security Note**: Never put the Supabase service-role secret, database passwords, or provider API keys into mobile `EXPO_PUBLIC_*` variables. Only the public anon key is safe on the client.

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

Migration script `001_initial_milestone2.py` sets up:
- `profiles`: UUID matching Supabase `auth.users(id)`, email, full_name, avatar_url.
- `trips`: UUID, owner_id (FK to profiles), title, destination, dates, budget, currency, travelers, status.
- `trip_members`: UUID, trip_id (FK to trips), profile_id (FK to profiles), role (OWNER, EDITOR, VIEWER), with unique constraint `(trip_id, profile_id)`.

---

## 4. Running Backend Automated Tests

Run the complete test suite (unit tests for JWT security + integration tests for profiles, trip CRUD, role permissions, and IDOR protection):
```powershell
cd d:\nnaik\Travio-Project\backend
.\.venv\Scripts\Activate.ps1
pytest -v
```

All 17 tests run in an isolated in-memory test database with zero external dependencies:
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
