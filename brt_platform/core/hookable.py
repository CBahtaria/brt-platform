import importlib
import logging
from typing import Any, Callable

from brt_platform.exceptions import PluginError

logger = logging.getLogger(__name__)


class Hookable:
    @staticmethod
    async def execute(core_func: Callable, *args: Any, context: Any, **kwargs: Any) -> Any:
        tenant_id = getattr(context, 'tenant_id', 'default')
        func_name = core_func.__name__
        module_path = f"custom_plugins.{tenant_id}.overrides"
        try:
            module = importlib.import_module(module_path)
            override = getattr(module, func_name, None)
            if override and callable(override):
                logger.info(f"Tenant override: {module_path}.{func_name}")
                return await override(core_func, *args, context=context, **kwargs)
        except ModuleNotFoundError:
            logger.debug(f"No overrides for tenant '{tenant_id}'.")
        except Exception as e:
            raise PluginError(f"Override error for tenant '{tenant_id}': {e}") from e
        return await core_func(*args, context=context, **kwargs)
