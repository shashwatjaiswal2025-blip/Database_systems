from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect, Depends
import asyncio
from dataclasses import dataclass, field

from sqlalchemy import select
from schemas import UserBase, vehicleBase, cameraBase, ParkingZoneBase, ParkingSlotBase
from database.db import get_session, engine, Base, User, Vehicle, Camera, ParkingZone, ParkingSlot
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix = "", tags=["new"])



#Add new vehicle to the database
@router.post("/vehicle")
async def add_vehicle(vehicle: vehicleBase, Session: AsyncSession = Depends(get_session)):
    stmt = select(Vehicle).where(Vehicle.plate_no == vehicle.plate_no)
    result = await Session.execute(stmt)
    if result.scalars().first():
        raise HTTPException(status_code=400, detail="Vehicle with the same plate number already exists")

    new_vehicle = Vehicle(
        plate_no=vehicle.plate_no,
        make=vehicle.make,
        model=vehicle.model,
        color=vehicle.color,
        registration_status=vehicle.registration_status,
        owner_id=vehicle.owner_id
    )

    Session.add(new_vehicle)
    await Session.commit()
    await Session.refresh(new_vehicle)
    return {"message": "Vehicle added successfully", "vehicle": vehicle}

# add camera
@router .post("/camera")
async def add_camera(camera: cameraBase, Session: AsyncSession = Depends(get_session)):
    stmt = select(Camera).where(Camera.camera_id == camera.camera_id)
    result = await Session.execute(stmt)
    if result.scalars().first():
        raise HTTPException(status_code=400, detail="Camera with the same camera_id already exists")

    new_camera = Camera(
        camera_id=camera.camera_id,
        location=camera.location,
        description=camera.description
    )

    Session.add(new_camera)
    await Session.commit()
    await Session.refresh(new_camera)
    return {"message": "Camera added successfully", "camera": camera}
