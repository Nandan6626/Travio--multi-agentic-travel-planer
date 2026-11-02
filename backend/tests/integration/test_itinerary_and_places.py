import uuid
from datetime import date, time, timedelta
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.trip import TripMember, TripRole
from tests.conftest import create_test_jwt


@pytest.mark.asyncio
async def test_places_creation_and_coordinate_validation(async_client: AsyncClient):
    user_id = uuid.uuid4()
    token = create_test_jwt(user_id=user_id)
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Successful place creation
    place_payload = {
        "name": "Eiffel Tower",
        "address": "Champ de Mars, 5 Av. Anatole France, 75007 Paris, France",
        "latitude": 48.8584,
        "longitude": 2.2945,
        "category": "monument",
        "rating": 4.7,
    }
    res = await async_client.post("/api/v1/places", headers=headers, json=place_payload)
    assert res.status_code == 201
    place_data = res.json()
    place_id = place_data["id"]
    assert place_data["name"] == "Eiffel Tower"
    assert place_data["latitude"] == 48.8584
    assert place_data["longitude"] == 2.2945

    # 2. Get place details
    get_res = await async_client.get(f"/api/v1/places/{place_id}", headers=headers)
    assert get_res.status_code == 200
    assert get_res.json()["name"] == "Eiffel Tower"

    # 3. Invalid coordinates (latitude > 90) -> 422
    bad_lat = {
        "name": "Invalid North Pole",
        "latitude": 95.0,
        "longitude": 0.0,
    }
    bad_res1 = await async_client.post("/api/v1/places", headers=headers, json=bad_lat)
    assert bad_res1.status_code == 422

    # 4. Invalid coordinates (longitude < -180) -> 422
    bad_lon = {
        "name": "Invalid West Pole",
        "latitude": 0.0,
        "longitude": -195.0,
    }
    bad_res2 = await async_client.post("/api/v1/places", headers=headers, json=bad_lon)
    assert bad_res2.status_code == 422


@pytest.mark.asyncio
async def test_itinerary_days_crud_and_date_validation(async_client: AsyncClient):
    user_id = uuid.uuid4()
    token = create_test_jwt(user_id=user_id)
    headers = {"Authorization": f"Bearer {token}"}

    today = date.today()
    start_date = today + timedelta(days=10)
    end_date = today + timedelta(days=15)

    # Create trip
    trip_res = await async_client.post(
        "/api/v1/trips",
        headers=headers,
        json={
            "title": "Swiss Vacation",
            "destination": "Zurich",
            "start_date": str(start_date),
            "end_date": str(end_date),
            "total_budget": "3000.00",
            "currency": "CHF",
            "traveler_count": 2,
        },
    )
    assert trip_res.status_code == 201
    trip_id = trip_res.json()["id"]

    # 1. Create Itinerary Day within trip dates
    day_res = await async_client.post(
        f"/api/v1/trips/{trip_id}/days",
        headers=headers,
        json={
            "day_number": 1,
            "date": str(start_date),
            "title": "Arrival & Old Town Exploration",
            "notes": "Pick up Swiss Travel Pass at airport",
        },
    )
    assert day_res.status_code == 201
    day_data = day_res.json()
    day_id = day_data["id"]
    assert day_data["day_number"] == 1
    assert day_data["title"] == "Arrival & Old Town Exploration"

    # 2. Invalid date outside trip (earlier than trip start_date) -> 422
    bad_date_res = await async_client.post(
        f"/api/v1/trips/{trip_id}/days",
        headers=headers,
        json={
            "day_number": 2,
            "date": str(start_date - timedelta(days=2)),
            "title": "Pre-trip day",
        },
    )
    assert bad_date_res.status_code == 422

    # 3. Duplicate day_number -> 422
    dup_day_res = await async_client.post(
        f"/api/v1/trips/{trip_id}/days",
        headers=headers,
        json={
            "day_number": 1,
            "date": str(start_date + timedelta(days=1)),
            "title": "Day 1 again",
        },
    )
    assert dup_day_res.status_code == 422

    # 4. List Days
    list_res = await async_client.get(f"/api/v1/trips/{trip_id}/days", headers=headers)
    assert list_res.status_code == 200
    assert len(list_res.json()) == 1

    # 5. Retrieve Day by day_id
    get_day_res = await async_client.get(f"/api/v1/days/{day_id}", headers=headers)
    assert get_day_res.status_code == 200
    assert get_day_res.json()["id"] == day_id

    # 6. Update Day
    patch_day_res = await async_client.patch(
        f"/api/v1/days/{day_id}",
        headers=headers,
        json={"title": "Arrival & Lake Cruise"},
    )
    assert patch_day_res.status_code == 200
    assert patch_day_res.json()["title"] == "Arrival & Lake Cruise"

    # 7. Delete Day
    del_day_res = await async_client.delete(f"/api/v1/days/{day_id}", headers=headers)
    assert del_day_res.status_code == 204

    # Confirm deletion
    get_after_del = await async_client.get(f"/api/v1/days/{day_id}", headers=headers)
    assert get_after_del.status_code == 404


@pytest.mark.asyncio
async def test_itinerary_activities_crud_and_schedule_validation(async_client: AsyncClient):
    user_id = uuid.uuid4()
    token = create_test_jwt(user_id=user_id)
    headers = {"Authorization": f"Bearer {token}"}

    today = date.today()
    start_date = today + timedelta(days=5)
    end_date = today + timedelta(days=10)

    # Trip and Day setup
    trip_res = await async_client.post(
        "/api/v1/trips",
        headers=headers,
        json={
            "title": "Tokyo Highlights",
            "destination": "Tokyo, Japan",
            "start_date": str(start_date),
            "end_date": str(end_date),
            "total_budget": "4000.00",
            "currency": "USD",
            "traveler_count": 1,
        },
    )
    trip_id = trip_res.json()["id"]

    day_res = await async_client.post(
        f"/api/v1/trips/{trip_id}/days",
        headers=headers,
        json={"day_number": 1, "date": str(start_date), "title": "Asakusa & Ueno"},
    )
    day_id = day_res.json()["id"]

    # Place setup
    place_res = await async_client.post(
        "/api/v1/places",
        headers=headers,
        json={
            "name": "Sensō-ji Temple",
            "address": "2-3-1 Asakusa, Taito City, Tokyo",
            "latitude": 35.7148,
            "longitude": 139.7967,
            "category": "historic",
        },
    )
    place_id = place_res.json()["id"]

    # 1. Add Activity 1 (09:00 - 11:30)
    act1_res = await async_client.post(
        f"/api/v1/days/{day_id}/items",
        headers=headers,
        json={
            "activity_name": "Visit Senso-ji",
            "description": "Ancient Buddhist temple with iconic Kaminarimon Gate",
            "category": "sightseeing",
            "start_time": "09:00:00",
            "end_time": "11:30:00",
            "estimated_cost": "15.00",
            "currency": "USD",
            "place_id": place_id,
        },
    )
    assert act1_res.status_code == 201
    act1 = act1_res.json()
    act1_id = act1["id"]
    assert act1["duration_minutes"] == 150
    assert act1["order_index"] == 0
    assert act1["place"]["name"] == "Sensō-ji Temple"

    # 2. Invalid Time Sequencing: end_time <= start_time -> 422
    bad_time_res = await async_client.post(
        f"/api/v1/days/{day_id}/items",
        headers=headers,
        json={
            "activity_name": "Time Machine Tour",
            "start_time": "14:00:00",
            "end_time": "13:00:00",
        },
    )
    assert bad_time_res.status_code == 422

    # 3. Overlapping Activity (10:00 - 12:00 overlaps with 09:00 - 11:30) -> 422
    overlap_res = await async_client.post(
        f"/api/v1/days/{day_id}/items",
        headers=headers,
        json={
            "activity_name": "Conflicting Tea Ceremony",
            "start_time": "10:00:00",
            "end_time": "12:00:00",
        },
    )
    assert overlap_res.status_code == 422
    assert "overlaps" in overlap_res.json()["detail"].lower()

    # 4. Add Activity 2 non-overlapping (12:00 - 13:30)
    act2_res = await async_client.post(
        f"/api/v1/days/{day_id}/items",
        headers=headers,
        json={
            "activity_name": "Lunch at Nakamise-dori",
            "category": "dining",
            "start_time": "12:00:00",
            "end_time": "13:30:00",
            "estimated_cost": "25.00",
            "currency": "USD",
        },
    )
    assert act2_res.status_code == 201
    act2_id = act2_res.json()["id"]
    assert act2_res.json()["order_index"] == 1

    # 5. Add Activity 3 (14:00 - 16:00)
    act3_res = await async_client.post(
        f"/api/v1/days/{day_id}/items",
        headers=headers,
        json={
            "activity_name": "Tokyo National Museum",
            "category": "museum",
            "start_time": "14:00:00",
            "end_time": "16:00:00",
            "estimated_cost": "20.00",
            "currency": "USD",
        },
    )
    assert act3_res.status_code == 201
    act3_id = act3_res.json()["id"]

    # 6. Retrieve single item
    item_get = await async_client.get(f"/api/v1/items/{act1_id}", headers=headers)
    assert item_get.status_code == 200
    assert item_get.json()["activity_name"] == "Visit Senso-ji"

    # 7. Update item
    patch_item = await async_client.patch(
        f"/api/v1/items/{act1_id}",
        headers=headers,
        json={"activity_name": "Sensō-ji Guided Cultural Tour"},
    )
    assert patch_item.status_code == 200
    assert patch_item.json()["activity_name"] == "Sensō-ji Guided Cultural Tour"

    # 8. Reorder activities: [act3_id, act1_id, act2_id]
    reorder_res = await async_client.patch(
        f"/api/v1/days/{day_id}/items/reorder",
        headers=headers,
        json={"item_ids": [act3_id, act1_id, act2_id]},
    )
    assert reorder_res.status_code == 200
    reordered_list = reorder_res.json()
    assert reordered_list[0]["id"] == act3_id
    assert reordered_list[0]["order_index"] == 0
    assert reordered_list[1]["id"] == act1_id
    assert reordered_list[1]["order_index"] == 1
    assert reordered_list[2]["id"] == act2_id
    assert reordered_list[2]["order_index"] == 2

    # 9. Delete item
    del_item = await async_client.delete(f"/api/v1/items/{act2_id}", headers=headers)
    assert del_item.status_code == 204
    get_del = await async_client.get(f"/api/v1/items/{act2_id}", headers=headers)
    assert get_del.status_code == 404


@pytest.mark.asyncio
async def test_reorder_transaction_rollback_on_failure(async_client: AsyncClient):
    user_id = uuid.uuid4()
    token = create_test_jwt(user_id=user_id)
    headers = {"Authorization": f"Bearer {token}"}

    today = date.today()
    trip_res = await async_client.post(
        "/api/v1/trips",
        headers=headers,
        json={
            "title": "Rollback Test Trip",
            "destination": "London",
            "start_date": str(today + timedelta(days=2)),
            "end_date": str(today + timedelta(days=6)),
            "total_budget": "1500.00",
            "currency": "GBP",
            "traveler_count": 1,
        },
    )
    trip_id = trip_res.json()["id"]

    day_res = await async_client.post(
        f"/api/v1/trips/{trip_id}/days",
        headers=headers,
        json={"day_number": 1, "date": str(today + timedelta(days=2)), "title": "Day 1"},
    )
    day_id = day_res.json()["id"]

    item1_res = await async_client.post(
        f"/api/v1/days/{day_id}/items",
        headers=headers,
        json={"activity_name": "Task A", "start_time": "09:00:00", "end_time": "10:00:00"},
    )
    item1_id = item1_res.json()["id"]

    item2_res = await async_client.post(
        f"/api/v1/days/{day_id}/items",
        headers=headers,
        json={"activity_name": "Task B", "start_time": "11:00:00", "end_time": "12:00:00"},
    )
    item2_id = item2_res.json()["id"]

    # Attempt reorder with an invalid/non-existent UUID
    bogus_id = uuid.uuid4()
    bad_reorder = await async_client.patch(
        f"/api/v1/days/{day_id}/items/reorder",
        headers=headers,
        json={"item_ids": [str(item2_id), str(bogus_id)]},
    )
    assert bad_reorder.status_code == 422

    # Verify original order is untouched (Transaction rollback preserved consistency)
    list_res = await async_client.get(f"/api/v1/days/{day_id}/items", headers=headers)
    assert list_res.status_code == 200
    items = list_res.json()
    assert items[0]["id"] == item1_id
    assert items[0]["order_index"] == 0
    assert items[1]["id"] == item2_id
    assert items[1]["order_index"] == 1



@pytest.mark.asyncio
async def test_itinerary_authorization_and_cross_user_rejection(
    async_client: AsyncClient, db_session: AsyncSession
):
    owner_id = uuid.uuid4()
    editor_id = uuid.uuid4()
    viewer_id = uuid.uuid4()
    stranger_id = uuid.uuid4()

    owner_token = create_test_jwt(user_id=owner_id, email="owner@travio.local")
    editor_token = create_test_jwt(user_id=editor_id, email="editor@travio.local")
    viewer_token = create_test_jwt(user_id=viewer_id, email="viewer@travio.local")
    stranger_token = create_test_jwt(user_id=stranger_id, email="stranger@travio.local")

    # Sync profiles
    for token in [editor_token, viewer_token, stranger_token]:
        await async_client.get("/api/v1/profiles/me", headers={"Authorization": f"Bearer {token}"})

    today = date.today()
    # Owner creates trip
    trip_res = await async_client.post(
        "/api/v1/trips",
        headers={"Authorization": f"Bearer {owner_token}"},
        json={
            "title": "Private Itinerary Trip",
            "destination": "Rome, Italy",
            "start_date": str(today + timedelta(days=1)),
            "end_date": str(today + timedelta(days=5)),
            "total_budget": "2000.00",
            "currency": "EUR",
            "traveler_count": 2,
        },
    )
    trip_id = uuid.UUID(trip_res.json()["id"])

    # Add editor and viewer
    db_session.add(TripMember(trip_id=trip_id, profile_id=editor_id, role=TripRole.EDITOR.value))
    db_session.add(TripMember(trip_id=trip_id, profile_id=viewer_id, role=TripRole.VIEWER.value))
    await db_session.commit()

    # 1. Editor can create a Day
    day_res = await async_client.post(
        f"/api/v1/trips/{trip_id}/days",
        headers={"Authorization": f"Bearer {editor_token}"},
        json={"day_number": 1, "date": str(today + timedelta(days=1)), "title": "Colosseum Day"},
    )
    assert day_res.status_code == 201
    day_id = day_res.json()["id"]

    # 2. Viewer CANNOT create a Day (403 Forbidden)
    viewer_create_day = await async_client.post(
        f"/api/v1/trips/{trip_id}/days",
        headers={"Authorization": f"Bearer {viewer_token}"},
        json={"day_number": 2, "date": str(today + timedelta(days=2)), "title": "Vatican"},
    )
    assert viewer_create_day.status_code == 403

    # 3. Viewer CAN view Days
    viewer_list_days = await async_client.get(
        f"/api/v1/trips/{trip_id}/days",
        headers={"Authorization": f"Bearer {viewer_token}"},
    )
    assert viewer_list_days.status_code == 200

    # 4. Stranger (Non-member) gets 403 Forbidden
    stranger_list = await async_client.get(
        f"/api/v1/trips/{trip_id}/days",
        headers={"Authorization": f"Bearer {stranger_token}"},
    )
    assert stranger_list.status_code == 403

    # 5. Editor creates Activity
    act_res = await async_client.post(
        f"/api/v1/days/{day_id}/items",
        headers={"Authorization": f"Bearer {editor_token}"},
        json={
            "activity_name": "Colosseum Tour",
            "start_time": "10:00:00",
            "end_time": "12:00:00",
        },
    )
    assert act_res.status_code == 201
    item_id = act_res.json()["id"]

    # 6. Viewer CANNOT edit or delete Activity (403)
    viewer_edit_act = await async_client.patch(
        f"/api/v1/items/{item_id}",
        headers={"Authorization": f"Bearer {viewer_token}"},
        json={"activity_name": "Hacked activity"},
    )
    assert viewer_edit_act.status_code == 403

    viewer_del_act = await async_client.delete(
        f"/api/v1/items/{item_id}",
        headers={"Authorization": f"Bearer {viewer_token}"},
    )
    assert viewer_del_act.status_code == 403

    # 7. Stranger CANNOT access item (403)
    stranger_get_act = await async_client.get(
        f"/api/v1/items/{item_id}",
        headers={"Authorization": f"Bearer {stranger_token}"},
    )
    assert stranger_get_act.status_code == 403
