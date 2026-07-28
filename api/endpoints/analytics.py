from fastapi import APIRouter, Depends, HTTPException
from models.schemas import AnalyticsRequest, AnalyticsResponse
from api.deps import get_analytics_service
from services.analytics_service import AnalyticsService
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/", response_model=AnalyticsResponse)
async def ask_analytics(
    request: AnalyticsRequest,
    analytics_service: AnalyticsService = Depends(get_analytics_service)
):
    try:
        answer = await analytics_service.answer_question(request.question, request.history)
        return AnalyticsResponse(question=request.question, answer=answer)
    except Exception as e:
        logger.error("Analytics request failed: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")
