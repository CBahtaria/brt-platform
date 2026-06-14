import asyncio
import hashlib
import logging

import httpx

from brt_platform.config import settings, RedisKeyPrefix

logger = logging.getLogger(__name__)


class PlatformAlerter:
    def __init__(self, redis_client):
        self.redis = redis_client

    async def emit_whatsapp_alert(self, severity: str, message: str, cooldown_minutes: int = 30):
        if not settings.CONSULTANT_WHATSAPP_NUMBER or not settings.WHATSAPP_GATEWAY_URL:
            logger.warning(f"WhatsApp not configured. Alert suppressed: [{severity}] {message[:80]}")
            return

        cooldown_key = f"{RedisKeyPrefix.ALERT_COOLDOWN}:{hashlib.md5(message.encode()).hexdigest()}"

        try:
            active = await asyncio.wait_for(self.redis.exists(cooldown_key), timeout=1.0)
            if active:
                logger.debug(f"Alert on cooldown: {message[:50]}")
                return
        except Exception as e:
            logger.warning(f"Redis cooldown check failed ({e}) — sending alert without cooldown")

        body = f"[BRT {severity.upper()}] {message}"
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                resp = await client.post(settings.WHATSAPP_GATEWAY_URL, json={
                    "number": settings.CONSULTANT_WHATSAPP_NUMBER,
                    "message": body,
                })
                resp.raise_for_status()
            logger.info(f"Alert sent: {body[:60]}")
            try:
                await self.redis.set(cooldown_key, "1", ex=cooldown_minutes * 60)
            except Exception:
                pass
        except Exception as e:
            logger.critical(f"Alert send failed: {e} | Original: {body}")
