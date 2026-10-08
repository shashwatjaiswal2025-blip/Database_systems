import asyncio
import os
import sys

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database.db import engine, Base, lifespan



app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)



@app.get("/")
async def root():
    return {"message": "Hello World"}

app.include_router(login.router)
app.include_router(game.router)