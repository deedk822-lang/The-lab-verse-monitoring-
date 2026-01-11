import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient
from unittest.mock import MagicMock

@pytest.fixture(scope="module")
def client():
    from api.server import app
    with TestClient(app) as c:
        yield c

@pytest.fixture(scope="module")
async def async_client():
    from api.server import app
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

@pytest.fixture
def mock_openai_client(mocker):
    mock_create = mocker.AsyncMock()
    mock_create.return_value.choices = [MagicMock(message=MagicMock(content='{"status": "mocked"}'))]

    mock_client_instance = MagicMock()
    mock_client_instance.chat.completions.create = mock_create

    mock_openai_class = mocker.patch("openai.AsyncOpenAI")
    mock_openai_class.return_value = mock_client_instance

    return mock_openai_class
