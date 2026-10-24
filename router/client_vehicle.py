from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect, Depends,status
import asyncio
from dataclasses import dataclass, field
from sqlalchemy import select
from schemas import UserBase, vehicleBase,Violations, violation_base
from database.db import get_db as get_session, User, Vehicle, Violation
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix = "", tags=["Citizen & Vehicle Management "])


#Add new user to the database
@router.post("/user", response_model=UserBase)
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

@router.get("/user/{user_id}",response_model=UserBase)
async def get_a_user( user_id:int,    Session: AsyncSession = Depends(get_session)):

    stmt = select(User).where(User.user_id== user_id)
    user = await Session.scalar(stmt)

    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail = f"User with id {user_id} not found")
    return user

@router.get("/user/vehicles",response_model=list[vehicleBase])
async def get_user_vehicles(user:UserBase, Session: AsyncSession = Depends(get_session)):
    stmt = select(Vehicle).where(Vehicle.user_id == user.user_id)
    vehicles = await Session.scalars(stmt)
    return list(vehicles)

@router.post("/vehicles",response_model=vehicleBase)
async def new_vehicle(vehicle: vehicleBase ,Session: AsyncSession = Depends(get_session)):
    stmt = select(Vehicle).where(Vehicle.plate_no == vehicle.plate_no)
    if Session.scalars(stmt) is not None:
        raise HTTPException(status_code= status.HTTP_409_CONFLICT, detail = f"Vehicle with plate number {vehicle.plate_no} already exists")

    new_vehicle = Vehicle(**vehicle.model_dump())
    Session.add(new_vehicle)
    await Session.commit()
    await Session.refresh(new_vehicle)
    return new_vehicle



@router.post("/vehicles/{plate_no}",response_model = vehicleBase)
async def get_vehicle_info(plate_no:int, Session: AsyncSession = Depends(get_session)):
    stmt = select(Vehicle).where(Vehicle.plate_no == plate_no)
    vehicle = await Session.scalar(stmt)
    if vehicle is  None:
        raise HTTPException(status_code= status.HTTP_404_NOT_FOUND, detail = f"Vehicle with plate number {plate_no} does not exists")

    return vehicle

@router.get("/vehicles/{plate_no}/history",response_model = list[violation_base])
async def get_vehicle_history(plate_no:str, Session: AsyncSession = Depends(get_session)):
    stmt = select(Vehicle).where(Vehicle.plate_no == plate_no)
    vehicle = await Session.scalar(stmt)
    if vehicle is  None:
        raise HTTPException(status_code= status.HTTP_404_NOT_FOUND, detail = f"Vehicle with plate number {plate_no} does not exists")
    stmt_violation = select(Violation).where(Violation.plate_no == plate_no)
    result = await Session.scalars(stmt_violation)
    
    return result.all()