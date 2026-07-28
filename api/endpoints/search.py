from fastapi import APIRouter, Depends, HTTPException
from models.schemas import SearchRequest, SearchResponse
from api.deps import get_query_service
from services.query_service import QueryService
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/", response_model=SearchResponse)
async def search_candidates(
    request: SearchRequest,
    query_service: QueryService = Depends(get_query_service)
):
    try:
        results = await query_service.search(request.query, request.top_k)
        return results
    except Exception as e:
        logger.error("Search request failed: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")
