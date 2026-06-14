import logging

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from brt_platform.core.rag_engine import BRTRagEngine, RequestContext
from brt_platform.exceptions import CircuitBreakerOpenError

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1", tags=["query"])
_engine = BRTRagEngine()


class QueryRequest(BaseModel):
    query: str
    top_k: int = 10


class QueryResponse(BaseModel):
    query: str
    results: list
    metadata: dict


@router.post("/query", response_model=QueryResponse)
async def query_endpoint(request: Request, payload: QueryRequest):
    if not payload.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty.")
    ctx = RequestContext(
        tenant_id=request.state.tenant_id,
        user_id=request.state.user_id,
    )
    try:
        result = await _engine.query(query=payload.query, context=ctx, top_k=payload.top_k)
        return QueryResponse(query=payload.query, results=result.chunks, metadata=result.metadata)
    except CircuitBreakerOpenError as e:
        raise HTTPException(status_code=503, detail=str(e))
