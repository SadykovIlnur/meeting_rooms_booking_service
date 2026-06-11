from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI

from app.api.v1 import admin, auth, bookings, rooms, slots
from app.db.database import db_dependency
from app.db.init_db import init_data


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_data()
    yield
    await db_dependency.close()


api_router = APIRouter(prefix="/api/v1")
api_router.include_router(admin.router)
api_router.include_router(auth.router)
api_router.include_router(bookings.router)
api_router.include_router(rooms.router)
api_router.include_router(slots.router)


app = FastAPI(title="Meeting Room Booking API", lifespan=lifespan)
app.include_router(api_router)


@app.get("/health")
async def health():
    return {"status": "ok"}
