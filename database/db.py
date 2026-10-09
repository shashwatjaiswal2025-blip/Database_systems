from datetime import datetime
from contextlib import asynccontextmanager
from decimal import Decimal
import os
from typing import List, Optional

from dotenv import load_dotenv
from fastapi import FastAPI
from sqlalchemy import DateTime, ForeignKey, Integer, MetaData, Numeric, String
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


load_dotenv()

POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", "5432"))
POSTGRES_DB = os.getenv("POSTGRES_DB", "citymoniter")
POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "password")


def _normalize_database_url(url: str) -> str:
    if url.startswith("postgressql://"):
        return url.replace("postgressql://", "postgresql+asyncpg://", 1)
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+asyncpg://", 1)
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return url


POSTGRES_URL = _normalize_database_url(
    os.getenv("DATABASE_URL")
    or os.getenv("Database_URL")
    or (
        f"postgresql+asyncpg://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
    )
)

engine = create_async_engine(POSTGRES_URL, echo=False)


class Base(DeclarativeBase):
    metadata = MetaData()


class User(Base):
    __tablename__ = "users"

    user_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    phone: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
    dl_no: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    gmail: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    middle_name: Mapped[Optional[str]] = mapped_column(String(100))
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)

    vehicles: Mapped[List["Vehicle"]] = relationship(
        back_populates="owner", cascade="all, delete-orphan"
    )
    reservations: Mapped[List["Reservation"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class Vehicle(Base):
    __tablename__ = "vehicles"

    plate_no: Mapped[str] = mapped_column(String(20), primary_key=True)
    make: Mapped[str] = mapped_column(String(100), nullable=False)
    model: Mapped[str] = mapped_column(String(100), nullable=False)
    color: Mapped[str] = mapped_column(String(50), nullable=False)
    registration_status: Mapped[str] = mapped_column(String(30), nullable=False)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.user_id"), nullable=False)

    owner: Mapped["User"] = relationship(back_populates="vehicles")
    reservations: Mapped[List["Reservation"]] = relationship(back_populates="vehicle")
    violations: Mapped[List["Violation"]] = relationship(
        back_populates="vehicle", cascade="all, delete-orphan"
    )


class ParkingZone(Base):
    __tablename__ = "parking_zones"

    zone_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    total_capacity: Mapped[int] = mapped_column(Integer, nullable=False)
    location_name: Mapped[str] = mapped_column(String(150), nullable=False)
    base_rate_per_hour: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)

    slots: Mapped[List["ParkingSlot"]] = relationship(
        back_populates="zone", cascade="all, delete-orphan"
    )


class ParkingSlot(Base):
    __tablename__ = "parking_slots"

    slot_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    sensor_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False)
    zone_id: Mapped[int] = mapped_column(ForeignKey("parking_zones.zone_id"), nullable=False)

    zone: Mapped["ParkingZone"] = relationship(back_populates="slots")
    reservations: Mapped[List["Reservation"]] = relationship(back_populates="slot")


class Reservation(Base):
    __tablename__ = "reservations"

    res_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    total_cost: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id"), nullable=False)
    plate_no: Mapped[str] = mapped_column(ForeignKey("vehicles.plate_no"), nullable=False)
    slot_id: Mapped[int] = mapped_column(ForeignKey("parking_slots.slot_id"), nullable=False)

    user: Mapped["User"] = relationship(back_populates="reservations")
    vehicle: Mapped["Vehicle"] = relationship(back_populates="reservations")
    slot: Mapped["ParkingSlot"] = relationship(back_populates="reservations")


class Camera(Base):
    __tablename__ = "cameras"

    camera_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    intersection: Mapped[str] = mapped_column(String(200), nullable=False)
    ip_address: Mapped[str] = mapped_column(String(45), unique=True, nullable=False)
    operational_status: Mapped[str] = mapped_column(String(30), nullable=False)

    violations: Mapped[List["Violation"]] = relationship(back_populates="camera")


class Violation(Base):
    __tablename__ = "violations"

    violation_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    rule_broken: Mapped[str] = mapped_column(String(255), nullable=False)
    violation_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    image_link: Mapped[Optional[str]] = mapped_column(String(500))
    plate_no: Mapped[str] = mapped_column(ForeignKey("vehicles.plate_no"), nullable=False)
    camera_id: Mapped[int] = mapped_column(ForeignKey("cameras.camera_id"), nullable=False)

    vehicle: Mapped["Vehicle"] = relationship(back_populates="violations")
    camera: Mapped["Camera"] = relationship(back_populates="violations")
    ticket: Mapped[Optional["Ticket"]] = relationship(
        back_populates="violation", uselist=False, cascade="all, delete-orphan"
    )


class Ticket(Base):
    __tablename__ = "tickets"

    ticket_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    fine_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    issue_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    due_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ticket_status: Mapped[str] = mapped_column(String(30), nullable=False)
    violation_id: Mapped[int] = mapped_column(
        ForeignKey("violations.violation_id"), unique=True, nullable=False
    )

    violation: Mapped["Violation"] = relationship(back_populates="ticket")
    appeals: Mapped[List["Appeal"]] = relationship(
        back_populates="ticket", cascade="all, delete-orphan"
    )


class Appeal(Base):
    __tablename__ = "appeals"

    appeals_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    reason_text: Mapped[str] = mapped_column(String(1000), nullable=False)
    appeal_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    appeal_decision: Mapped[Optional[str]] = mapped_column(String(1000))
    ticket_id: Mapped[int] = mapped_column(ForeignKey("tickets.ticket_id"), nullable=False)

    ticket: Mapped["Ticket"] = relationship(back_populates="appeals")


SessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)

async def get_db():
    async with SessionLocal() as session:
        yield session
        
@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


async def get_db():
    async with SessionLocal() as session:
        yield session

