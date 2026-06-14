from pydantic_settings import BaseSettings, SettingsConfigDict


class RedisKeyPrefix:
    ALERT_COOLDOWN = "brt:alert:cooldown"
    PAYSTACK_PROCESSED = "brt:paystack:processed"
    PAYSTACK_LOCK = "brt:paystack:lock"
    QDRANT_COLLECTION_LOCK = "brt:qdrant:create"
    CIRCUIT_BREAKER_STATE = "brt:cb:state"
    CIRCUIT_BREAKER_FAILURES = "brt:cb:failures"
    RATE_LIMIT = "brt:ratelimit"
    TENANT_SESSION = "brt:session"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    BRT_TENANT_ID: str = "brt-default"
    BRT_ENV: str = "production"
    DEBUG: bool = False

    ANTHROPIC_API_KEY: str | None = None

    QDRANT_URL: str = "http://localhost:6333"
    QDRANT_API_KEY: str | None = None
    EMBEDDING_MODEL: str = "BAAI/bge-large-en-v1.5"
    SPARSE_MODEL: str = "prithivida/Splade_PP_en_v1"
    RERANKER_MODEL: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"

    REDIS_URL: str = "redis://localhost:6379/0"

    CONSULTANT_WHATSAPP_NUMBER: str | None = None
    WHATSAPP_GATEWAY_URL: str | None = None
    SLACK_WEBHOOK_URL: str | None = None

    KAFKA_BOOTSTRAP_SERVERS: str = "kafka:9092"
    KAFKA_KRAFT_CLUSTER_ID: str = ""
    CLICKHOUSE_HOST: str = "clickhouse"
    CLICKHOUSE_DB: str = "brt_platform"
    CLICKHOUSE_USER: str = "brt_user"
    CLICKHOUSE_PASSWORD: str = ""

    SUPABASE_URL: str | None = None
    SUPABASE_SERVICE_ROLE_KEY: str | None = None

    S3_ENDPOINT: str | None = None
    S3_BUCKET: str = "brt-platform-artifacts"
    AWS_ACCESS_KEY_ID: str | None = None
    AWS_SECRET_ACCESS_KEY: str | None = None


settings = Settings()
