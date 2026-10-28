import uuid
from datetime import date, timedelta
from decimal import Decimal
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.trip import TripMember, TripRole
from tests.conftest import create_test_jwt


@pytest.mark.asyncio
async def test_unauthenticated_profile_access_returns_401(async_client: AsyncClient):
    response = await async_client.get("/api/v1/profiles/me")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_and_sync_profile(async_client: AsyncClient):
    user_id = uuid.uuid4()
    token = create_test_jwt(user_id=user_id, email="alice@travio.local")
    headers = {"Authorization": f"Bearer {token}"}

    # 1. First fetch auto-initializes profile
    res = await async_client.get("/api/v1/profiles/me", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["id"] == str(user_id)
    assert data["email"] == "alice@travio.local"
    assert data["full_name"] == "Test User"

    # 2. Sync profile
    sync_res = await async_client.post(
        "/api/v1/profiles/me",
        headers=headers,
        json={"full_name": "Alice Explorer", "avatar_url": "https://example.com/avatar.png"},
    )
    assert sync_res.status_code == 200
    updated_data = sync_res.json()
    assert updated_data["full_name"] == "Alice Explorer"
    assert updated_data["avatar_url"] == "https://example.com/avatar.png"


@pytest.mark.asyncio
async def test_trip_crud_and_ownership(async_client: AsyncClient):
    user_id = uuid.uuid4()
    token = create_test_jwt(user_id=user_id, email="owner@travio.local")
    headers = {"Authorization": f"Bearer {token}"}

    today = date.today()
    trip_payload = {
        "title": "Kyoto Exploration",
        "destination": "Kyoto, Japan",
        "start_date": str(today + timedelta(days=30)),
        "end_date": str(today + timedelta(days=37)),
        "total_budget": "3500.00",
        "currency": "USD",
        "traveler_count": 2,
    }

    # Create Trip
    res = await async_client.post("/api/v1/trips", headers=headers, json=trip_payload)
    assert res.status_code == 201
    created_trip = res.json()
    trip_id = created_trip["id"]
    assert created_trip["owner_id"] == str(user_id)
    assert created_trip["user_role"] == "OWNER"
    assert len(created_trip["members"]) == 1
    assert created_trip["members"][0]["role"] == "OWNER"

    # List Trips
    list_res = await async_client.get("/api/v1/trips", headers=headers)
    assert list_res.status_code == 200
    list_data = list_res.json()
    assert list_data["total"] == 1
    assert list_data["trips"][0]["id"] == trip_id

    # Get Single Trip
    get_res = await async_client.get(f"/api/v1/trips/{trip_id}", headers=headers)
    assert get_res.status_code == 200
    assert get_res.json()["title"] == "Kyoto Exploration"

    # Update Trip
    update_res = await async_client.patch(
        f"/api/v1/trips/{trip_id}",
        headers=headers,
        json={"title": "Kyoto Cultural Deep Dive", "total_budget": "4000.00"},
    )
    assert update_res.status_code == 200
    assert update_res.json()["title"] == "Kyoto Cultural Deep Dive"
    assert update_res.json()["total_budget"] == "4000.00"

    # Delete Trip
    del_res = await async_client.delete(f"/api/v1/trips/{trip_id}", headers=headers)
    assert del_res.status_code == 204

    # Confirm deletion
    get_after_del = await async_client.get(f"/api/v1/trips/{trip_id}", headers=headers)
    assert get_after_del.status_code == 404


@pytest.mark.asyncio
async def test_cross_user_access_rejection_idor(async_client: AsyncClient):
    # User A creates a trip
    user_a = uuid.uuid4()
    token_a = create_test_jwt(user_id=user_a, email="user_a@travio.local")
    res_a = await async_client.post(
        "/api/v1/trips",
        headers={"Authorization": f"Bearer {token_a}"},
        json={
            "title": "Private Vacation",
            "destination": "Paris, France",
            "start_date": str(date.today() + timedelta(days=10)),
            "end_date": str(date.today() + timedelta(days=15)),
            "total_budget": "2000.00",
            "currency": "EUR",
            "traveler_count": 1,
        },
    )
    assert res_a.status_code == 201
    trip_id = res_a.json()["id"]

    # User B tries to read User A's trip -> MUST be 403 Forbidden
    user_b = uuid.uuid4()
    token_b = create_test_jwt(user_id=user_b, email="user_b@travio.local")
    res_b = await async_client.get(
        f"/api/v1/trips/{trip_id}",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert res_b.status_code == 403
    assert "permission" in res_b.json()["detail"].lower()

    # User B tries to update User A's trip -> MUST be 403 Forbidden
    patch_b = await async_client.patch(
        f"/api/v1/trips/{trip_id}",
        headers={"Authorization": f"Bearer {token_b}"},
        json={"title": "Hacked Title"},
    )
    assert patch_b.status_code == 403

    # User B tries to delete User A's trip -> MUST be 403 Forbidden
    del_b = await async_client.delete(
        f"/api/v1/trips/{trip_id}",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert del_b.status_code == 403


@pytest.mark.asyncio
async def test_role_hierarchy_permissions(async_client: AsyncClient, db_session: AsyncSession):
    # User A (Owner) creates trip
    user_a = uuid.uuid4()
    token_a = create_test_jwt(user_id=user_a, email="owner_a@travio.local")
    create_res = await async_client.post(
        "/api/v1/trips",
        headers={"Authorization": f"Bearer {token_a}"},
        json={
            "title": "Team Retreat",
            "destination": "Zurich, Switzerland",
            "start_date": str(date.today() + timedelta(days=20)),
            "end_date": str(date.today() + timedelta(days=25)),
            "total_budget": "5000.00",
            "currency": "CHF",
            "traveler_count": 4,
        },
    )
    trip_id = uuid.UUID(create_res.json()["id"])

    # User B (Editor) and User C (Viewer)
    user_b = uuid.uuid4()
    user_c = uuid.uuid4()
    token_b = create_test_jwt(user_id=user_b, email="editor_b@travio.local")
    token_c = create_test_jwt(user_id=user_c, email="viewer_c@travio.local")

    # Sync profiles in DB
    await async_client.get("/api/v1/profiles/me", headers={"Authorization": f"Bearer {token_b}"})
    await async_client.get("/api/v1/profiles/me", headers={"Authorization": f"Bearer {token_c}"})

    # Add User B as EDITOR, User C as VIEWER
    db_session.add(TripMember(trip_id=trip_id, profile_id=user_b, role=TripRole.EDITOR.value))
    db_session.add(TripMember(trip_id=trip_id, profile_id=user_c, role=TripRole.VIEWER.value))
    await db_session.commit()

    # 1. Test EDITOR (User B)
    # Can view
    res_b_get = await async_client.get(f"/api/v1/trips/{trip_id}", headers={"Authorization": f"Bearer {token_b}"})
    assert res_b_get.status_code == 200
    assert res_b_get.json()["user_role"] == "EDITOR"

    # Can update
    res_b_patch = await async_client.patch(
        f"/api/v1/trips/{trip_id}",
        headers={"Authorization": f"Bearer {token_b}"},
        json={"title": "Updated by Editor B"},
    )
    assert res_b_patch.status_code == 200

    # CANNOT delete (403)
    res_b_del = await async_client.delete(f"/api/v1/trips/{trip_id}", headers={"Authorization": f"Bearer {token_b}"})
    assert res_b_del.status_code == 403

    # 2. Test VIEWER (User C)
    # Can view
    res_c_get = await async_client.get(f"/api/v1/trips/{trip_id}", headers={"Authorization": f"Bearer {token_c}"})
    assert res_c_get.status_code == 200
    assert res_c_get.json()["user_role"] == "VIEWER"

    # CANNOT update (403)
    res_c_patch = await async_client.patch(
        f"/api/v1/trips/{trip_id}",
        headers={"Authorization": f"Bearer {token_c}"},
        json={"title": "Attempted by Viewer"},
    )
    assert res_c_patch.status_code == 403

    # CANNOT delete (403)
    res_c_del = await async_client.delete(f"/api/v1/trips/{trip_id}", headers={"Authorization": f"Bearer {token_c}"})
    assert res_c_del.status_code == 403


@pytest.mark.asyncio
async def test_input_validation_rules(async_client: AsyncClient):
    user_id = uuid.uuid4()
    token = create_test_jwt(user_id=user_id)
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Invalid Dates: end_date < start_date
    res_dates = await async_client.post(
        "/api/v1/trips",
        headers=headers,
        json={
            "title": "Time Traveler Trip",
            "destination": "London",
            "start_date": "2026-10-15",
            "end_date": "2026-10-10",
            "total_budget": "1000.00",
            "currency": "USD",
            "traveler_count": 1,
        },
    )
    assert res_dates.status_code == 422

    # 2. Negative Budget
    res_budget = await async_client.post(
        "/api/v1/trips",
        headers=headers,
        json={
            "title": "Debt Trip",
            "destination": "London",
            "start_date": "2026-10-15",
            "end_date": "2026-10-20",
            "total_budget": "-500.00",
            "currency": "USD",
            "traveler_count": 1,
        },
    )
    assert res_budget.status_code == 422

    # 3. Invalid traveler count (< 1)
    res_travelers = await async_client.post(
        "/api/v1/trips",
        headers=headers,
        json={
            "title": "Ghost Trip",
            "destination": "London",
            "start_date": "2026-10-15",
            "end_date": "2026-10-20",
            "total_budget": "500.00",
            "currency": "USD",
            "traveler_count": 0,
        },
    )
    assert res_travelers.status_code == 422
