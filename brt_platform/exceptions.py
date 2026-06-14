class BRTError(Exception):
    def __init__(self, message: str = "An internal BRT Platform error occurred.", detail: str | None = None):
        self.message = message
        self.detail = detail
        super().__init__(self.message)

class ConfigurationError(BRTError):
    pass

class TenantNotFoundError(BRTError):
    pass

class CollectionCreationError(BRTError):
    pass

class EmbeddingError(BRTError):
    pass

class PluginError(BRTError):
    pass

class PluginSandboxError(PluginError):
    pass

class CircuitBreakerOpenError(BRTError):
    pass
