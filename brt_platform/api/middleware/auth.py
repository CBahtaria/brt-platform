import logging

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from brt_platform.config import settings
from brt_platform.exceptions import TenantNotFoundError

logger = logging.getLogger(__name__)

PUBLIC_PATHS = {"/health", "/docs", "/openapi.json", "/redoc"}


class TenantContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.url.path in PUBLIC_PATHS:
            return await call_next(request)

        # Phase 0: Header-based tenancy for demos.
        # Phase 1+: Replace with Supabase JWT validation.
        tenant_id = request.headers.get("X-Tenant-ID") or settings.BRT_TENANT_ID
        if not tenant_id:
            raise TenantNotFoundError("X-Tenant-ID header is required.")

        request.state.tenant_id = tenant_id
        request.state.user_id = request.headers.get("X-User-ID", "demo-user")
        logger.debug(f"Request: {request.method} {request.url.path} | tenant={tenant_id}")
        return await call_next(request)
