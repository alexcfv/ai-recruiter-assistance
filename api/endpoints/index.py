from fastapi import APIRouter, Depends, HTTPException
from models.schemas import IndexResponse, IndexRequest
from api.deps import get_index_service
from services.index_service import IndexService
import os
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/", response_model=IndexResponse)
async def index_path(
    request: IndexRequest,
    index_service: IndexService = Depends(get_index_service)
):
    path = request.path.strip()
    if not os.path.exists(path):
        raise HTTPException(status_code=400, detail=f"Path does not exist: {path}")
    
    try:
        if os.path.isdir(path):
            result = await index_service.index_folder(path)
        else:
            res = await index_service.index_file(path)
            result = {
                'new_profiles': [res] if res else [],
                'new_chunks': 0, 
                'files_count': 1
            }
            
        return IndexResponse(
            status="success",
            message=f"Successfully indexed: {path}",
            indexed_count=len(result.get('new_profiles', [])),
            new_chunks=result.get('new_chunks', 0),
            files_processed=result.get('files_count', 0) or len(result.get('new_profiles', []))
        )
    except Exception as e:
        logger.error("Index request failed for path %s: %s", path, e, exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")
