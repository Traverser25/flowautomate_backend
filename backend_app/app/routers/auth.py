# app/routers/auth.py
from fastapi import APIRouter, Depends, status
from app.schemas.user import UserCreate
from app.schemas.auth import Token
from app.models.user import UserInDB
from app.db.mongo import mongo
from app.core.security import hash_password, verify_password, create_access_token
from app.core.config import get_settings
from app.core.logger import get_logger
from app.core.response import APIResponse

from fastapi.security import OAuth2PasswordRequestForm
from fastapi import HTTPException

router = APIRouter(prefix="/auth", tags=["auth"])
settings = get_settings()
logger = get_logger(__name__)

@router.post("/register")
async def register(user: UserCreate):
    logger.info(f"Attempting to register user: {user.username}")
    
    existing = await mongo.db.users.find_one({"username": user.username})
    if existing:
        logger.warning(f"Registration failed. Username already exists: {user.username}")
        return APIResponse.fail(error="Username already exists", message="Registration failed")

    hashed_pwd = await hash_password(user.password)
    user_doc = UserInDB(username=user.username, hashed_password=hashed_pwd, name=user.name)
    await mongo.db.users.insert_one(user_doc.dict(by_alias=True))
    logger.info(f"User registered successfully: {user.username}")

    token = await create_access_token(
        subject=str(user_doc.id),
        extra={"username": user.username, "role": user_doc.role}
    )
    logger.info(f"Access token created for user: {user.username}")
    return APIResponse.success(data={"access_token": token}, message="User registered successfully")


@router.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    logger.info(f"Login attempt for username: {form_data.username}")
    
    user_doc = await mongo.db.users.find_one({"username": form_data.username})
    if not user_doc:
        logger.warning(f"Login failed. Invalid username: {form_data.username}")
        return APIResponse.fail(error="Invalid username or password", message="Login failed")

    valid = await verify_password(form_data.password, user_doc["hashed_password"])
    if not valid:
        logger.warning(f"Login failed. Invalid password for username: {form_data.username}")
        return APIResponse.fail(error="Invalid username or password", message="Login failed")

    token = await create_access_token(
        subject=str(user_doc["_id"]),
        extra={"username": user_doc["username"], "role": user_doc.get("role", "user")}
    )
    logger.info(f"User logged in successfully: {form_data.username}")
    return APIResponse.success(data={"access_token": token}, message="Login successful")
