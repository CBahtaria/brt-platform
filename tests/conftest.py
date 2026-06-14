import pytest
import asyncio


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# Platform markers
def pytest_configure(config):
    config.addinivalue_line("markers", "requires_cuda: skip if no CUDA GPU")
    config.addinivalue_line("markers", "requires_linux: skip on non-Linux")
    config.addinivalue_line("markers", "skip_windows: skip on Windows")
