import pytest
from unittest.mock import AsyncMock, patch
from brt_platform.core.rag_engine import BRTRagEngine, RequestContext


@pytest.fixture
def context():
    return RequestContext(tenant_id="test-tenant", user_id="test-user")


@pytest.mark.asyncio
async def test_rag_engine_handles_empty_results(context):
    engine = BRTRagEngine()
    with patch.object(engine, '_hybrid_search', return_value=[]):
        with patch.object(engine.reranker, 'rerank', return_value=[]):
            result = await engine._query_impl(query="test", context=context, top_k=5)
    assert result.chunks == []
    assert "model" in result.metadata


@pytest.mark.asyncio
async def test_request_context_tenant_id():
    ctx = RequestContext(tenant_id="my-tenant")
    assert ctx.tenant_id == "my-tenant"
    assert ctx.user_id is None
