from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect, Depends,status
import asyncio
from dataclasses import dataclass, field
from sqlalchemy import select
from schemas import telemetry, reservation_resquest,ParkingZoneBase,ParkingSlotBase,parking
from database.db import get_db as get_session, ParkingSlot,ParkingZone,Reservation
from sqlalchemy.ext.asyncio import AsyncSession

"""
2. Smart Parking Management 
Handles parking lots, sensor updates, and driver reservations.
Zones & Slots
Method	Endpoint	Description
GET		/parking/zones		List all parking zones with real-time occupancy counts
POST		/parking/zones		Add a new parking zone (Admin)
GET		/parking/zones/{zone_id}/available-slots	Find currently free slots in a specific zone
PATCH 	/parking/slots/{sensor_id}/telemetry	IoT Endpoint: Update slot status (VACANT, OCCUPIED) sent by parking sensors

Reservations
Method	Endpoint	Description
POST		/reservations/	Reserve a parking slot (calculates cost based on base_rate_per_hour * hours)
GET		/reservations/{res_id}	Get reservation details & receipt
POST		/reservations/{res_id}/cancel	Cancel reservation and free the slot
GET		/users/{user_id}/reservations	View user's past and upcoming reservations

"""



router = APIRouter(prefix = "", tags=["Parking Management"])

@router.get("/parking/zones", response_model=list[parking])
async def list_parking_zones(Session: AsyncSession = Depends(get_session)):
    stmt = select(ParkingZone)
    result = await Session.execute(stmt)
    zones = result.scalars().all()
    return zones

@router.post("/parking/zones")
async def new_parking_zone(zone: ParkingZoneBase, Session: AsyncSession = Depends(get_session)):
    new_zone = ParkingZone(**zone.model_dump())
    Session.add(new_zone)
    await Session.commit()
    await Session.refresh(new_zone)
    return new_zone

@router.get("/parking/zones/{zone_id}/available-slots",response_model=list[ParkingSlotBase])
async def available_slots(zone_id: int, Session: AsyncSession = Depends(get_session)):
    stmt = select(ParkingSlot).where(ParkingSlot.zone_id == zone_id, ParkingSlot.status == "VACANT")
    result = await Session.execute(stmt)
    slots = result.scalars().all()
    return slots

@router.patch("/parking/slots/telemetry", status_code=status.HTTP_200_OK)
async def update_slot_telemetry(slot_details: telemetry, session: AsyncSession = Depends(get_session)):



    stmt = select(ParkingSlot).where(
        ParkingSlot.zone_id == slot_details.zone_id,
        ParkingSlot.slot_id == slot_details.slot_id,
    )

    result = await session.execute(stmt)
    slot = result.scalars().first()  

    if not slot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Slot {slot_details.slot_id} in zone {slot_details.zone_id} not found",
        )

    slot.status = "OCCUPIED" if slot_details.status else "EMPTY"


    await session.commit()
    await session.refresh(slot)

    return {
        "message": "Telemetry updated successfully",
        "slot_id": slot.slot_id,
        "zone_id": slot.zone_id,
        "status": slot.status,
    }

@router.post("/reservations")
async def reserve_slot(reservation_details: reservation_resquest, session: AsyncSession = Depends(get_session)):

    if reservation_details.start_time >= reservation_details.end_time:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Start time must be before end time",
        )


    stmt = select(ParkingSlot).where(
        ParkingSlot.zone_id == reservation_details.zone_id,
        ParkingSlot.slot_id == reservation_details.slot_id,
    )

    result = await session.execute(stmt)
    slot = result.scalars().first()

    if not slot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Slot {reservation_details.slot_id} in zone {reservation_details.zone_id} not found",
        )

    stmt = select(ParkingZone).where(ParkingZone.zone_id == reservation_details.zone_id)
    result_zone = await session.execute(stmt)
    zone = result_zone.scalars().first()

    stmt_res = select(Reservation).where(
            Reservation.zone_id == reservation_details.zone_id,
            Reservation.slot_id == reservation_details.slot_id,
            Reservation.start_time < reservation_details.end_time,
            Reservation.end_time > reservation_details.start_time
        )

    result_res = await session.execute(stmt_res)
    existing_reservation = result_res.scalars().first()

    if existing_reservation :
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Slot {reservation_details.slot_id} in zone {reservation_details.zone_id} is already reserved",
        )

    


    duration = reservation_details.end_time-reservation_details.start_time
    duration_hr= float(duration.total_seconds()/3600)

    cost =round(duration_hr * float(zone.base_rate_per_hour), 2)

    new_reservation = Reservation(
    **reservation_details.model_dump(),
    total_cost=cost
    )

    session.add(new_reservation)
    await session.commit()
    await session.refresh(new_reservation)

    return new_reservation

@router.get("/reservations/{res_id}")
async def get_reservation(res_id: int, session: AsyncSession = Depends(get_session)):
    stmt = select(Reservation).where(Reservation.res_id == res_id)
    result = await session.execute(stmt)
    reservation = result.scalars().first()

    if not reservation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Reservation {res_id} not found",
        )

    return reservation

@router.post("/reservations/{res_id}/cancel")
async def cancel_reservation(res_id: int, session: AsyncSession = Depends(get_session)):
    stmt = select(Reservation).where(Reservation.res_id == res_id)
    result = await session.execute(stmt)
    reservation = result.scalars().first()
    if not reservation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Reservation {res_id} not found",
            )
    session.delete(reservation)
    await session.commit()
    return {"message": f"Reservation {res_id} cancelled successfully"}

@router.get("/users/{user_id}/reservations")
async def get_user_reservations(user_id: int, session: AsyncSession = Depends(get_session)):
    stmt = select(Reservation).where(Reservation.user_id == user_id)
    result = await session.execute(stmt)
    reservations = result.scalars().all()
    return reservations