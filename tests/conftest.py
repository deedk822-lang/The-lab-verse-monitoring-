import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient
from unittest.mock import MagicMock

@pytest.fixture(scope="module")
def client():
    """
    Provide a synchronous TestClient connected to the FastAPI app from api.server for use in tests.
    
    Yields:
        TestClient: A TestClient instance bound to `api.server.app`.
    """
    from api.server import app
    with TestClient(app) as c:
        yield c

@pytest.fixture(scope="module")
async def async_client():
    """
    Provide an httpx AsyncClient bound to the FastAPI app for use in tests.
    
    Yields:
        httpx.AsyncClient: An AsyncClient instance mounted to the FastAPI `app` with base_url "http://test". The client is closed automatically when the fixture's context exits.
    """
    from api.server import app
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

@pytest.fixture
def mock_openai_client(mocker):
    """
    Create and return a patched `openai.AsyncOpenAI` class configured for tests.
    
    The patched class returns a mock client whose `chat.completions.create` is an `AsyncMock`
    that yields a response with `choices` containing a message whose `content` is the JSON
    string '{"status": "mocked"}'.
    
    Parameters:
        mocker: The pytest-mock `mocker` fixture used to create and apply the patch.
    
    Returns:
        The patched `openai.AsyncOpenAI` class (the object returned by `mocker.patch`).
    """
    mock_create = mocker.AsyncMock()
    mock_create.return_value.choices = [MagicMock(message=MagicMock(content='{"status": "mocked"}'))]

    mock_client_instance = MagicMock()
    mock_client_instance.chat.completions.create = mock_create

    mock_openai_class = mocker.patch("openai.AsyncOpenAI")
    mock_openai_class.return_value = mock_client_instance

    return mock_openai_class