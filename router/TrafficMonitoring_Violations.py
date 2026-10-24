from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect, Depends,status
import asyncio
from dataclasses import dataclass, field
from sqlalchemy import select
from schemas import Violations, camerabase, new_camera, violation_request, violation_base, ticket_base
from database.db import Ticket, Vehicle, get_db as get_session, ParkingSlot,ParkingZone,Reservation
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import timedelta

router = APIRouter(prefix = "", tags=["Traffic Monitoring & Violations "])


"""
3. Traffic Monitoring & Violations (/api/v1/traffic & /api/v1/violations)
Handles camera streams/metadata, automated violation detection, and ticketing.
Cameras & Surveillance

Method	Endpoint	Description
GET		/cameras/	List all cameras and their operational statuses
POST		/cameras/	Register a new camera at an intersection (Admin)
PATCH		/cameras/{camera_id}/status	Heartbeat / update status (ONLINE, OFFLINE, MAINTENANCE)

Violations & Tickets
Method	Endpoint	Description
POST		/violations/	Ingestion Endpoint: Triggered by ANPR/Camera service when a rule is broken. Automatically generates a Ticket record.
GET		/violations/	List violations with filters (plate_no, camera_id, date_range)
GET		/violations/{violation_id}	View violation details and snapshot (image_link)
GET		/tickets/{ticket_id}	Get ticket details and fine balance
GET		/tickets/search	Search unpaid tickets (e.g., query params: ?plate_no=XYZ&dl_no=ABC)
POST		/tickets/{ticket_id}/pay	Mock or trigger fine payment (updates ticket_status to PAID)
Ḥ

"""

@router.get("/cameras",response_model=list[camerabase])
async def get_cameras(session: AsyncSession = Depends(get_session)):

    result = await session.execute(select(ParkingZone))
    cameras = result.scalars().all()
    return cameras

@router.post("/cameras",status_code=status.HTTP_201_CREATED)
async def register_camera(camera: new_camera, session: AsyncSession = Depends(get_session)):
    new_camera = ParkingZone(
        location_name=camera.location_name,
        status=camera.status,
        ip_address=camera.ip_address
    )
    session.add(new_camera)
    await session.commit()
    return {"message": "Camera registered successfully."}



@router.post("/violations",status_code=status.HTTP_201_CREATED)
async def report_violation(violation: violation_request, session: AsyncSession = Depends(get_session)):
    stmt_vehicle = select(Vehicle).where(Vehicle.plate_no == violation.plate_no)
    result_vehicle = await session.execute(stmt_vehicle)
    vehicle = result_vehicle.scalar_one_or_none()
    if not vehicle:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vehicle not found.")

    if violation.rule_broken not in ["speeding", "red_light_violation", "illegal_parking", "other"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid rule broken.")

    if violation.fine_amount is None:
        if violation.rule_broken == "speeding":
            violation.fine_amount = 100.00

        elif violation.rule_broken == "red_light_violation":
            violation.fine_amount = 150.00
        elif violation.rule_broken == "illegal_parking":
            violation.fine_amount = 50.00
        else:
            violation.fine_amount = 0.00

    new_violation = Vehicle(**violation.model_dump())
    session.add(new_violation)
    await session.commit()
    await session.refresh(new_violation)


    ticket = Ticket(
        fine_amount=violation.fine_amount,
        issue_date=new_violation.violation_time,
        due_date=new_violation.violation_time + timedelta(days=30),
        ticket_status="unpaid",
        user_id=vehicle.owner_id,
        violation_id=new_violation.violation_id
    )
    session.add(ticket)
    await session.commit()
    return new_violation

@router.get("/violations/{violation_id}", response_model=violation_base)
async def get_violation_details(violation_id: int, session: AsyncSession = Depends(get_session)):
    stmt = select(Vehicle).where(Vehicle.violation_id == violation_id)
    result = await session.execute(stmt)
    violation = result.scalar_one_or_none()
    if not violation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Violation not found.")
    return violation

@router.get("/tickets/{ticket_id}", response_model=ticket_base)
async def get_ticket_details(ticket_id: int, session: AsyncSession = Depends(get_session)):
    stmt = select(Ticket).where(Ticket.ticket_id == ticket_id)
    result = await session.execute(stmt)
    ticket = result.scalar_one_or_none()
    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found.")
    return ticket

@router.get("/tickets/search", response_model=list[ticket_base])
async def search_unpaid_tickets(plate_no: str | None = None, dl_no: str | None = None, session: AsyncSession = Depends(get_session)):
    stmt = select(Ticket).join(Vehicle).where(Ticket.ticket_status == "unpaid")
    if plate_no:
        stmt = stmt.where(Vehicle.plate_no == plate_no)
    if dl_no:
        stmt = stmt.where(Vehicle.owner.has(dl_no=dl_no))
    result = await session.execute(stmt)
    tickets = result.scalars().all()
    return tickets

@router.post("/tickets/{ticket_id}/pay")
async def pay_ticket(ticket_id: int, session: AsyncSession = Depends(get_session)):
    stmt = select(Ticket).where(Ticket.ticket_id == ticket_id)
    result = await session.execute(stmt)
    ticket = result.scalar_one_or_none()
    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found.")
    if ticket.ticket_status == "paid":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Ticket is already paid.")

    ticket.ticket_status = "paid"
    await session.commit()
    return {"message": "Ticket payment successful."}
