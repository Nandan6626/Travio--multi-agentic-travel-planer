import uuid
from datetime import time, timedelta
from typing import List, Tuple, Optional
from sqlalchemy import select, and_, func
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from app.models.trip import Trip, TripRole
from app.models.itinerary import ItineraryDay, ItineraryItem
from app.models.place import Place
from app.schemas.itinerary import (
    ItineraryDayCreate,
    ItineraryDayUpdate,
    ItineraryItemCreate,
    ItineraryItemUpdate,
)
from app.services.trip_service import TripService


def calculate_duration_minutes(start_t: time, end_t: time) -> int:
    """Calculates difference in minutes between two time objects."""
    s_min = start_t.hour * 60 + start_t.minute
    e_min = end_t.hour * 60 + end_t.minute
    return e_min - s_min


def times_overlap(s1: time, e1: time, s2: time, e2: time) -> bool:
    """Returns True if [s1, e1) overlaps with [s2, e2)."""
    return max(s1, s2) < min(e1, e2)


class ItineraryService:
    @staticmethod
    async def create_day(
        db: AsyncSession,
        trip_id: uuid.UUID,
        user_id: uuid.UUID,
        data: ItineraryDayCreate,
    ) -> ItineraryDay:
        # 1. Require EDITOR role on trip
        trip, _ = await TripService.get_permitted_trip(
            db=db, trip_id=trip_id, user_id=user_id, min_role=TripRole.EDITOR
        )

        # 2. Validate date against trip dates
        if data.date < trip.start_date or data.date > trip.end_date:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Day date {data.date} must be within trip dates ({trip.start_date} to {trip.end_date})",
            )

        # 3. Check for day_number collision
        existing_stmt = select(ItineraryDay).where(
            ItineraryDay.trip_id == trip_id,
            ItineraryDay.day_number == data.day_number,
        )
        existing = (await db.execute(existing_stmt)).scalar_one_or_none()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Day number {data.day_number} already exists for this trip",
            )

        day = ItineraryDay(
            trip_id=trip_id,
            day_number=data.day_number,
            date=data.date,
            title=data.title,
            notes=data.notes,
        )
        db.add(day)
        await db.commit()
        await db.refresh(day)

        # Reload with items
        stmt = (
            select(ItineraryDay)
            .options(selectinload(ItineraryDay.items).selectinload(ItineraryItem.place))
            .where(ItineraryDay.id == day.id)
        )
        return (await db.execute(stmt)).scalar_one()

    @staticmethod
    async def list_days(
        db: AsyncSession,
        trip_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> List[ItineraryDay]:
        # Require VIEWER role on trip
        await TripService.get_permitted_trip(
            db=db, trip_id=trip_id, user_id=user_id, min_role=TripRole.VIEWER
        )

        stmt = (
            select(ItineraryDay)
            .options(selectinload(ItineraryDay.items).selectinload(ItineraryItem.place))
            .where(ItineraryDay.trip_id == trip_id)
            .order_by(ItineraryDay.day_number.asc())
        )
        res = await db.execute(stmt)
        return list(res.scalars().all())

    @staticmethod
    async def get_permitted_day(
        db: AsyncSession,
        day_id: uuid.UUID,
        user_id: uuid.UUID,
        min_role: TripRole = TripRole.VIEWER,
    ) -> Tuple[ItineraryDay, TripRole]:
        stmt = (
            select(ItineraryDay)
            .options(selectinload(ItineraryDay.items).selectinload(ItineraryItem.place))
            .where(ItineraryDay.id == day_id)
        )
        day = (await db.execute(stmt)).scalar_one_or_none()
        if not day:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Itinerary day not found")

        _, role = await TripService.get_permitted_trip(
            db=db, trip_id=day.trip_id, user_id=user_id, min_role=min_role
        )
        return day, role

    @staticmethod
    async def update_day(
        db: AsyncSession,
        day_id: uuid.UUID,
        user_id: uuid.UUID,
        data: ItineraryDayUpdate,
    ) -> ItineraryDay:
        day, _ = await ItineraryService.get_permitted_day(
            db=db, day_id=day_id, user_id=user_id, min_role=TripRole.EDITOR
        )

        # Retrieve trip to validate date if date is being updated
        if data.date is not None:
            trip_stmt = select(Trip).where(Trip.id == day.trip_id)
            trip = (await db.execute(trip_stmt)).scalar_one()
            if data.date < trip.start_date or data.date > trip.end_date:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Day date {data.date} must be within trip dates ({trip.start_date} to {trip.end_date})",
                )
            day.date = data.date

        if data.day_number is not None and data.day_number != day.day_number:
            existing_stmt = select(ItineraryDay).where(
                ItineraryDay.trip_id == day.trip_id,
                ItineraryDay.day_number == data.day_number,
                ItineraryDay.id != day.id,
            )
            existing = (await db.execute(existing_stmt)).scalar_one_or_none()
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Day number {data.day_number} already exists for this trip",
                )
            day.day_number = data.day_number

        if data.title is not None:
            day.title = data.title
        if data.notes is not None:
            day.notes = data.notes

        await db.commit()
        await db.refresh(day)
        return day

    @staticmethod
    async def delete_day(
        db: AsyncSession,
        day_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> None:
        day, _ = await ItineraryService.get_permitted_day(
            db=db, day_id=day_id, user_id=user_id, min_role=TripRole.EDITOR
        )
        await db.delete(day)
        await db.commit()

    # --- Item Operations ---

    @staticmethod
    async def create_item(
        db: AsyncSession,
        day_id: uuid.UUID,
        user_id: uuid.UUID,
        data: ItineraryItemCreate,
    ) -> ItineraryItem:
        day, _ = await ItineraryService.get_permitted_day(
            db=db, day_id=day_id, user_id=user_id, min_role=TripRole.EDITOR
        )

        # 1. Validate Place if place_id provided
        if data.place_id:
            place_res = await db.execute(select(Place).where(Place.id == data.place_id))
            if not place_res.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Place with id {data.place_id} does not exist",
                )

        # 2. Check for overlapping activities within the day
        items_stmt = select(ItineraryItem).where(ItineraryItem.day_id == day_id)
        current_items = list((await db.execute(items_stmt)).scalars().all())

        for existing in current_items:
            if times_overlap(data.start_time, data.end_time, existing.start_time, existing.end_time):
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=(
                        f"Activity time ({data.start_time.strftime('%H:%M')} - {data.end_time.strftime('%H:%M')}) "
                        f"overlaps with existing activity '{existing.activity_name}' "
                        f"({existing.start_time.strftime('%H:%M')} - {existing.end_time.strftime('%H:%M')})"
                    ),
                )

        # 3. Determine order_index
        if data.order_index is not None:
            order_idx = data.order_index
        else:
            max_order_stmt = select(func.coalesce(func.max(ItineraryItem.order_index), -1)).where(
                ItineraryItem.day_id == day_id
            )
            max_order = (await db.execute(max_order_stmt)).scalar()
            order_idx = max_order + 1

        duration_mins = calculate_duration_minutes(data.start_time, data.end_time)

        item = ItineraryItem(
            day_id=day_id,
            place_id=data.place_id,
            activity_name=data.activity_name,
            description=data.description,
            category=data.category,
            start_time=data.start_time,
            end_time=data.end_time,
            duration_minutes=duration_mins,
            order_index=order_idx,
            estimated_cost=data.estimated_cost,
            currency=data.currency,
        )
        db.add(item)
        await db.commit()

        # Reload with place relationship
        load_stmt = (
            select(ItineraryItem)
            .options(selectinload(ItineraryItem.place))
            .where(ItineraryItem.id == item.id)
        )
        return (await db.execute(load_stmt)).scalar_one()

    @staticmethod
    async def list_items(
        db: AsyncSession,
        day_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> List[ItineraryItem]:
        await ItineraryService.get_permitted_day(
            db=db, day_id=day_id, user_id=user_id, min_role=TripRole.VIEWER
        )

        stmt = (
            select(ItineraryItem)
            .options(selectinload(ItineraryItem.place))
            .where(ItineraryItem.day_id == day_id)
            .order_by(ItineraryItem.order_index.asc())
        )
        res = await db.execute(stmt)
        return list(res.scalars().all())

    @staticmethod
    async def get_permitted_item(
        db: AsyncSession,
        item_id: uuid.UUID,
        user_id: uuid.UUID,
        min_role: TripRole = TripRole.VIEWER,
    ) -> Tuple[ItineraryItem, TripRole]:
        stmt = (
            select(ItineraryItem)
            .options(selectinload(ItineraryItem.place))
            .where(ItineraryItem.id == item_id)
        )
        item = (await db.execute(stmt)).scalar_one_or_none()
        if not item:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Activity item not found")

        _, role = await ItineraryService.get_permitted_day(
            db=db, day_id=item.day_id, user_id=user_id, min_role=min_role
        )
        return item, role

    @staticmethod
    async def update_item(
        db: AsyncSession,
        item_id: uuid.UUID,
        user_id: uuid.UUID,
        data: ItineraryItemUpdate,
    ) -> ItineraryItem:
        item, _ = await ItineraryService.get_permitted_item(
            db=db, item_id=item_id, user_id=user_id, min_role=TripRole.EDITOR
        )

        new_start = data.start_time or item.start_time
        new_end = data.end_time or item.end_time

        if new_end <= new_start:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Activity end_time must be later than start_time",
            )

        # Check overlapping activities (excluding itself)
        if data.start_time is not None or data.end_time is not None:
            other_items_stmt = select(ItineraryItem).where(
                ItineraryItem.day_id == item.day_id,
                ItineraryItem.id != item.id,
            )
            other_items = list((await db.execute(other_items_stmt)).scalars().all())
            for other in other_items:
                if times_overlap(new_start, new_end, other.start_time, other.end_time):
                    raise HTTPException(
                        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                        detail=(
                            f"Updated time ({new_start.strftime('%H:%M')} - {new_end.strftime('%H:%M')}) "
                            f"overlaps with existing activity '{other.activity_name}' "
                            f"({other.start_time.strftime('%H:%M')} - {other.end_time.strftime('%H:%M')})"
                        ),
                    )

        if data.place_id is not None:
            place_res = await db.execute(select(Place).where(Place.id == data.place_id))
            if not place_res.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Place with id {data.place_id} does not exist",
                )
            item.place_id = data.place_id

        if data.activity_name is not None:
            item.activity_name = data.activity_name
        if data.description is not None:
            item.description = data.description
        if data.category is not None:
            item.category = data.category
        if data.start_time is not None:
            item.start_time = data.start_time
        if data.end_time is not None:
            item.end_time = data.end_time
        item.duration_minutes = calculate_duration_minutes(new_start, new_end)
        if data.order_index is not None:
            item.order_index = data.order_index
        if data.estimated_cost is not None:
            item.estimated_cost = data.estimated_cost
        if data.currency is not None:
            item.currency = data.currency

        await db.commit()
        await db.refresh(item)

        load_stmt = (
            select(ItineraryItem)
            .options(selectinload(ItineraryItem.place))
            .where(ItineraryItem.id == item.id)
        )
        return (await db.execute(load_stmt)).scalar_one()

    @staticmethod
    async def delete_item(
        db: AsyncSession,
        item_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> None:
        item, _ = await ItineraryService.get_permitted_item(
            db=db, item_id=item_id, user_id=user_id, min_role=TripRole.EDITOR
        )
        await db.delete(item)
        await db.commit()

    @staticmethod
    async def reorder_items(
        db: AsyncSession,
        day_id: uuid.UUID,
        user_id: uuid.UUID,
        item_ids: List[uuid.UUID],
    ) -> List[ItineraryItem]:
        """Safely reorders activities in a single database transaction."""
        await ItineraryService.get_permitted_day(
            db=db, day_id=day_id, user_id=user_id, min_role=TripRole.EDITOR
        )

        items_stmt = select(ItineraryItem).where(ItineraryItem.day_id == day_id)
        items_in_day = {item.id: item for item in (await db.execute(items_stmt)).scalars().all()}

        # Verify all provided item_ids belong to this day
        for i_id in item_ids:
            if i_id not in items_in_day:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Item ID {i_id} does not belong to day {day_id}",
                )

        if len(item_ids) != len(items_in_day):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Reorder request must include all {len(items_in_day)} activities for this day",
            )

        # Two-phase update to avoid unique constraint collision on (day_id, order_index)
        # Phase 1: Set temporary negative indices
        for idx, i_id in enumerate(item_ids):
            items_in_day[i_id].order_index = -(idx + 1000)
        await db.flush()

        # Phase 2: Set final sequential indices
        for idx, i_id in enumerate(item_ids):
            items_in_day[i_id].order_index = idx

        await db.commit()

        # Reload ordered list
        stmt = (
            select(ItineraryItem)
            .options(selectinload(ItineraryItem.place))
            .where(ItineraryItem.day_id == day_id)
            .order_by(ItineraryItem.order_index.asc())
        )
        res = await db.execute(stmt)
        return list(res.scalars().all())

