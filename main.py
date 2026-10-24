from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database.db import engine, Base, lifespan
from router.appeals_disputes import router as appeals_router
from router.client_vehicle import router as reservations_router
from router.parking import router as parking_router





app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(parking_router, prefix="", tags=["Parking Management"])
app.include_router(appeals_router, prefix="", tags=["Appeals & Disputes"])
app.include_router(reservations_router, prefix="", tags=["Reservations"])
app.include_router(parking_router, prefix="", tags=["Parking"])

@app.get("/")
async def root():
    return {"message": "Hello World"}
