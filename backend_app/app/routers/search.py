from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordBearer
from app.core.security import decode_token
from app.schemas.search import SearchRequest
from app.services.search_service import search_query_service
from app.core.response import APIResponse
from app.core.logger import get_logger

router = APIRouter(prefix="/search", tags=["search"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")
logger = get_logger(__name__)

# Centralized exception using APIResponse
def raise_api_exception(message: str, error: str = None, status_code: int = 401):
    logger.warning(f"{message} | Error: {error}")
    return APIResponse.fail(error=error or message, message=message, status_code=status_code)

async def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = await decode_token(token)
        logger.info(f"Token decoded successfully: {payload.get('username')}")
        username = payload.get("username")
        if username is None:
            return raise_api_exception("Invalid token", error="Username not found", status_code=401)
        return payload
    except Exception as e:
        return raise_api_exception("Invalid token", error=str(e), status_code=401)


@router.post("/")
async def search_users(request_body: SearchRequest, current_user: dict = Depends(get_current_user)):
    try:
        query = request_body.query

        if not query:
            logger.warning(f"Empty search query from user: {current_user.get('username')}")
            return APIResponse.fail(error="Query is empty", message="Query cannot be empty")
        top_k_paragraphs = getattr(request_body, "top_k_paragraphs", 5)
        top_k_tables = getattr(request_body, "top_k_tables", 10)

        logger.info(f"Search requested by user: {current_user.get('username')} | Query: {query}")

        result = await search_query_service(
            query=query,
            top_k_paragraphs=top_k_paragraphs,
            top_k_tables=top_k_tables
        )

        logger.info("Search executed successfully")
        return APIResponse.success(data=result, message="Search executed successfully")

    except Exception as e:
        logger.error(f"Search failed: {str(e)}")
        return APIResponse.fail(error=str(e), message="Search failed")
