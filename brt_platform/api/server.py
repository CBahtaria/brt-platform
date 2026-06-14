import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from brt_platform.config import settings
from brt_platform.core.connection_pool import ConnectionPool
from brt_platform.core.embedder import Embedder
from brt_platform.utils.platform import PlatformDetector
from brt_platform.api.middleware.auth import TenantContextMiddleware
from brt_platform.api.routes import health, query, ingest
from brt_platform.exceptions import BRTError

logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"BRT Platform starting [{settings.BRT_ENV}]")
    detector = PlatformDetector()
    detector.apply_optimal_config()
    await Embedder.load_models()
    logger.info("BRT Platform ready.")
    yield
    await ConnectionPool.close_all()
    logger.info("BRT Platform shut down.")


app = FastAPI(
    title="BRT Platform API",
    version="0.1.0",
    description="SADC AI Orchestration & RAG Platform",
    lifespan=lifespan,
)

app.add_middleware(TenantContextMiddleware)
app.include_router(health.router)
app.include_router(query.router)
app.include_router(ingest.router)


@app.exception_handler(BRTError)
async def brt_error_handler(request: Request, exc: BRTError):
    return JSONResponse(status_code=400, content={"error": exc.message, "detail": exc.detail})


@app.exception_handler(Exception)
async def generic_error_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(status_code=500, content={"error": "Internal server error."})
