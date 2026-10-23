from datetime import datetime

from pydantic import BaseModel
from typing import Optional,Literal

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
    registration_status: Literal["active", "pending", "expired"] = "pending" # to be changed with better options if ideas come
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

class Violations(BaseModel):
    plate_no: str

class parking(BaseModel):
    zone_id: int
    total_capacity: int
    location_name: str
    base_rate_per_hour: float


class telemetry(BaseModel):
    zone_id:int
    slot_id:int
    status:bool # 1 for ocuupied 0 for empty

class reservation_resquest(BaseModel):
    user_id:int
    zone_id:int
    slot_id:int
    start_time:datetime
    end_time:datetime

class reservation_base_submit(BaseModel):
    res_id:int
    user_id:int
    zone_id:int
    slot_id:int
    start_time:datetime
    end_time:datetime
    total_cost:float

class new_camera(BaseModel):
    location_name:str
    status:Literal["ONLINE","OFFLINE","MAINTENANCE"]
    ip_address:str

class camerabase(new_camera):
    camera_id:str

class violation_request(BaseModel):
    rule_broken:Literal["speeding","red_light_violation","illegal_parking","other"]
    img_link:str
    vehicle_plate:str
    reporter_id:int
    fine_amount:float | None = None

class violation_base(violation_request):
    violation_id:int
    violation_time:datetime

class ticket_app(BaseModel):
    violation_id:int
    user_id:int
    fine_amount:float
    status:Literal["paid","unpaid"]

class ticket_base(ticket_app):
    ticket_id:int
    issue_date:datetime
    due_date:datetime

class appeal_request(BaseModel):
    ticket_id:int
    reason:str
