from brt_platform.config import RedisKeyPrefix, settings


def test_redis_key_prefixes_use_brt_namespace():
    for attr in ["ALERT_COOLDOWN", "PAYSTACK_PROCESSED", "CIRCUIT_BREAKER_STATE"]:
        value = getattr(RedisKeyPrefix, attr)
        assert value.startswith("brt:"), f"{attr} must start with 'brt:'"


def test_default_settings():
    assert settings.BRT_ENV in ("production", "development")
    assert settings.EMBEDDING_MODEL == "BAAI/bge-large-en-v1.5"
