from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect, Depends
import asyncio
from dataclasses import dataclass, field

from sqlalchemy import select
from schemas import UserBase, vehicleBase, cameraBase, ParkingZoneBase, ParkingSlotBase
from database.db import get_session, engine, Base, User, Vehicle, Camera, ParkingZone, ParkingSlot
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix = "new", tags=["new"])


#Add new user to the database
@router.post("/user")
async def add_user(user: UserBase, Session: AsyncSession = Depends(get_session)):
    
    #checks if user already exists
    stmt = select(User).where(User.phone == user.phone or User.dl_no == user.dl_no or User.gmail == user.gmail)
    result = await Session.execute(stmt)
    if result.scalars().first():
        raise HTTPException(status_code=400, detail="User with the same phone, dl_no or gmail already exists")

    # If user doesn't exist, create a new user
    new_user = User(
        first_name=user.first_name,
        middle_name=user.middle_name,
        last_name=user.last_name,
        phone=user.phone,
        dl_no=user.dl_no,
        gmail=user.gmail
    )

    
    Session.add(new_user)
    await Session.commit()
    await Session.refresh(new_user)
    return new_user

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
