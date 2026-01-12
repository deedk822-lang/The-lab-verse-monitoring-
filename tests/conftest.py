import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient
from unittest.mock import MagicMock

@pytest.fixture(scope="module")
def client():
    """
    Provide a synchronous TestClient for the FastAPI app used in tests and ensure proper setup and teardown.
    
    Returns:
        TestClient: A TestClient instance bound to api.server.app for use in test cases.
    """
    from api.server import app
    with TestClient(app) as c:
        yield c

@pytest.fixture(scope="module")
async def async_client():
    """
    Provide an httpx AsyncClient instance bound to the FastAPI app for asynchronous tests.
    
    Yields an AsyncClient configured with the application imported from api.server and a base URL of "http://test".
    
    Returns:
        httpx.AsyncClient: an asynchronous HTTP client connected to the FastAPI app.
    """
    from api.server import app
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

@pytest.fixture
def mock_openai_client(mocker):
    """
    Provide a patched openai.AsyncOpenAI class that yields a mocked client for tests.
    
    The mocked client exposes chat.completions.create as an AsyncMock which returns an object whose `choices` list contains a message with the JSON string '{"status": "mocked"}'.
    
    Parameters:
        mocker: The pytest-mock fixture used to create AsyncMock and patch `openai.AsyncOpenAI`.
    
    Returns:
        mock_openai_class: The patched `openai.AsyncOpenAI` class; instantiating it returns the mocked client instance.
    """
    mock_create = mocker.AsyncMock()
    mock_create.return_value.choices = [MagicMock(message=MagicMock(content='{"status": "mocked"}'))]

    mock_client_instance = MagicMock()
    mock_client_instance.chat.completions.create = mock_create

    mock_openai_class = mocker.patch("openai.AsyncOpenAI")
    mock_openai_class.return_value = mock_client_instance

    return mock_openai_class