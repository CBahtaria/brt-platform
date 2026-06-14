import asyncio
import json
import logging
from typing import AsyncGenerator

logger = logging.getLogger(__name__)


async def rag_sse_stream(chunks: list[dict]) -> AsyncGenerator[str, None]:
    """Yields SSE-formatted events for RAG results."""
    for chunk in chunks:
        yield f"data: {json.dumps(chunk)}\n\n"
        await asyncio.sleep(0)
    yield "data: [DONE]\n\n"
