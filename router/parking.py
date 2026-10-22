from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect, Depends,status
import asyncio
from dataclasses import dataclass, field
from sqlalchemy import select
from schemas import UserBase, vehicleBase,Violations,telemetry
from database.db import get_session, ParkingSlot,ParkingZone
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

@router.get("/parking/zones", responce_model=list[ParkingZone])
async def list_parking_zones(Session: AsyncSession = Depends(get_session)):
    stmt = select(ParkingZone)
    result = await Session.execute(stmt)
    zones = result.scalars().all()
    return zones

@router.post("/parking/zones")
async def new_parking_zone(zone: ParkingZone, Session: AsyncSession = Depends(get_session)):
    new_zone = ParkingZone(**zone.model_dump())
    Session.add(new_zone)
    await Session.commit()
    await Session.refresh(new_zone)
    return new_zone

@router.get("/parking/zones/{zone_id}/available-slots",response_model=list[ParkingSlot])
async def available_slots(zone_id: int, Session: AsyncSession = Depends(get_session)):
    stmt = select(ParkingSlot).where(ParkingSlot.zone_id == zone_id, ParkingSlot.status == "VACANT")
    result = await Session.execute(stmt)
    slots = result.scalars().all()
    return slots

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


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
