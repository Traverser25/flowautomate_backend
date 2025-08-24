# app/main.py
from fastapi import FastAPI
from app.db.mongo import connect_to_mongo, close_mongo_connection
from app.routers import auth, users, health,search
from app.core.config import get_settings

settings = get_settings()

app = FastAPI(title=settings.APP_NAME, debug=settings.DEBUG)


app.include_router(auth.router)

app.include_router(health.router)

app.include_router(search.router)
@app.on_event("startup")
async def startup_db():
    await connect_to_mongo()


@app.on_event("shutdown")
async def shutdown_db():
    await close_mongo_connection()
