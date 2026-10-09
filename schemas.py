from pydantic import BaseModel
from typing import Optional

class UserBase(BaseModel):
    phone: str
    dl_no: str
    gmail: str
    first_name: str
    middle_name: Optional[str] = None
    last_name: str

class vehicleBase(BaseModel):
    plate_no: str
    make: str
    model: str
    color: str
    registration_status: str
    owner_id: int

class cameraBase(BaseModel):
    camera_id: str
    location_name: str
    status: str
    zone_id: int

class ParkingZoneBase(BaseModel):
    total_capacity: int
    location_name: str
    base_rate_per_hour: float

class ParkingSlotBase(BaseModel):
    sensor_id: str
    status: str
    zone_id: int

