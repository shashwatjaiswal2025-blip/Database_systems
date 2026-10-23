from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect, Depends,status
import asyncio
from dataclasses import dataclass, field
from sqlalchemy import select
from schemas import UserBase, appeal_request, vehicleBase,Violations,telemetry, reservation_resquest
from database.db import get_session, ParkingSlot,ParkingZone,Reservation
from sqlalchemy.ext.asyncio import AsyncSession
from database.db import Ticket, Appeal
from typing import Literal




"""
4. Appeals & Disputes (/api/v1/appeals)
Allows citizens to contest fines and city officials to review them.
Method	Endpoint		Description
POST		/tickets/{ticket_id}	/appeals	Citizen submits an appeal with a reason
GET		/appeals/		List pending appeals for city officers to review
GET		/appeals/{appeals_id}	View appeal details alongside the violation image
PATCH	/appeals/{appeals_id}/review	Officer approves/rejects appeal (updates ticket to WAIVED or REJECTED)
"""


router  = APIRouter(prefix = "", tags=["Appeals & Disputes"])

@router.post("/tickets/{ticket_id}/appeals")
async def submit_appeal(ticket_id: int, appeal: appeal_request, Session: AsyncSession = Depends(get_session)):
    # Check if the ticket exists
    stmt = select(Ticket).where(Ticket.ticket_id == ticket_id)
    result = await Session.execute(stmt)
    ticket = result.scalars().first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    # Create a new appeal
    new_appeal = Appeal(
        reason_text=appeal.reason_text,
        appeal_date=appeal.appeal_date,
        ticket_id=ticket_id
    )

    Session.add(new_appeal)
    await Session.commit()
    await Session.refresh(new_appeal)
    return {"message": "Appeal submitted successfully", "appeal": new_appeal}

@router.get("/appeals", response_model=list[Appeal])
async def list_appeals(Session: AsyncSession = Depends(get_session)):
    stmt = select(Appeal)
    result = await Session.execute(stmt)
    appeals = result.scalars().all()
    return appeals

@router.get("/appeals/{appeals_id}", response_model=Appeal)
async def get_appeal(appeals_id: int, Session: AsyncSession = Depends(get_session)):
    stmt = select(Appeal).where(Appeal.appeals_id == appeals_id)
    result = await Session.execute(stmt)
    appeal = result.scalars().first()
    if not appeal:
        raise HTTPException(status_code=404, detail="Appeal not found")
    return appeal

@router.patch("/appeals/{appeals_id}/review")
async def review_appeal(appeals_id: int, appeal_decision: Literal["approved", "rejected"], Session: AsyncSession = Depends(get_session)):

    stmt = select(Appeal).where(Appeal.appeals_id == appeals_id)
    result = await Session.execute(stmt)
    appeal = result.scalars().first()
    if not appeal:
        raise HTTPException(status_code=404, detail="Appeal not found")

    appeal.appeal_decision = appeal_decision
    await Session.commit()
    await Session.refresh(appeal)

    ticket_stmt = select(Ticket).where(Ticket.ticket_id == appeal.ticket_id)
    ticket_result = await Session.execute(ticket_stmt)
    ticket = ticket_result.scalars().first()

    if appeal_decision.lower() == "approved":
        ticket.ticket_status = "WAIVED"
    elif appeal_decision.lower() == "rejected":
        ticket.ticket_status = "REJECTED"
    
    await Session.commit()
    return {"message": "Appeal reviewed successfully", "appeal": appeal, "ticket": ticket}