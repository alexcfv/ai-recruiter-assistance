from fastapi import Request
from services.query_service import QueryService
from services.analytics_service import AnalyticsService
from services.index_service import IndexService

def get_query_service(request: Request) -> QueryService:
    return request.app.state.query_service

def get_analytics_service(request: Request) -> AnalyticsService:
    return request.app.state.analytics_service

def get_index_service(request: Request) -> IndexService:
    return request.app.state.index_service
