"""
Pytest configuration and fixtures for backend tests.

This module provides reusable fixtures for testing:
- Mock Azure services (CosmosDB, Blob Storage, OpenAI)
- Test Quart app instance
- Sample test data
"""

import asyncio
import gc
import os
import sys
from datetime import datetime, timezone
from typing import AsyncGenerator

import pytest
from quart import Quart


def pytest_configure(config):
    """Set minimal env vars required for backend imports before test collection.

    Only sets variables absolutely required to import settings.py without errors.
    All other test environment configuration is handled by the mock_environment fixture.
    """
    # AZURE_OPENAI_ENDPOINT is required by _AzureOpenAISettings validator
    os.environ.setdefault("AZURE_OPENAI_ENDPOINT", "https://test.openai.azure.com/")

    # Add the backend directory to the Python path
    tests_dir = os.path.dirname(os.path.abspath(__file__))
    backend_dir = os.path.join(os.path.dirname(tests_dir), 'backend')
    if backend_dir not in sys.path:
        sys.path.insert(0, backend_dir)

    # Set Windows event loop policy (fixes pytest-asyncio auto mode compatibility)
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())


def pytest_sessionfinish(session, exitstatus):  # noqa: ARG001
    """Clean up any remaining async resources after test session.

    This helps prevent 'Unclosed client session' warnings from aiohttp
    that can occur when Azure SDK or other async clients aren't fully closed.

    Args:
        session: pytest Session object (required by hook signature)
        exitstatus: exit status code (required by hook signature)
    """
    del session, exitstatus  # Unused but required by pytest hook signature
    # Force garbage collection to trigger cleanup of any unclosed sessions
    gc.collect()

    # Close any remaining event loops
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            loop.stop()
        if not loop.is_closed():
            loop.close()
    except Exception:
        # Ignore exceptions during event loop cleanup (loop may already be closed)
        pass


@pytest.fixture(scope="function", autouse=True)
def mock_environment(monkeypatch):
    """Set test environment variables with correct names matching settings.py.

    Uses monkeypatch for proper test isolation - each test starts with a clean
    environment and changes are automatically reverted after the test.
    """
    env_vars = {
        # Azure OpenAI (required - _AzureOpenAISettings)
        "AZURE_OPENAI_ENDPOINT": "https://test-openai.openai.azure.com/",
        "AZURE_ENV_OPENAI_API_VERSION": "2024-08-01-preview",
        "AZURE_OPENAI_API_VERSION": "2024-08-01-preview",  # Legacy for backward compatibility test

        # Azure Cosmos DB (_CosmosSettings uses AZURE_COSMOS_ prefix)
        "AZURE_COSMOS_ENDPOINT": "https://test-cosmos.documents.azure.com:443/",
        "AZURE_COSMOS_DATABASE_NAME": "test-db",

        # Chat History (_ChatHistorySettings uses AZURE_COSMOSDB_ prefix)
        "AZURE_COSMOSDB_DATABASE": "test-db",
        "AZURE_COSMOSDB_ACCOUNT": "test-cosmos",
        "AZURE_COSMOSDB_CONVERSATIONS_CONTAINER": "conversations",
        "AZURE_COSMOSDB_PRODUCTS_CONTAINER": "products",

        # Azure Blob Storage (_StorageSettings uses AZURE_BLOB_ prefix)
        "AZURE_BLOB_ACCOUNT_NAME": "teststorage",
        "AZURE_BLOB_PRODUCT_IMAGES_CONTAINER": "product-images",
        "AZURE_BLOB_GENERATED_IMAGES_CONTAINER": "generated-images",

        # Azure AI Search (_SearchSettings uses AZURE_AI_SEARCH_ prefix)
        "AZURE_AI_SEARCH_ENDPOINT": "https://test-search.search.windows.net",
        "AZURE_AI_SEARCH_PRODUCTS_INDEX": "products",
        "AZURE_AI_SEARCH_IMAGE_INDEX": "product-images",

        # AI Foundry (disabled for tests)
        "USE_FOUNDRY": "false",

        # Admin API (empty = development mode, no auth required)
        "ADMIN_API_KEY": "",
    }

    for key, value in env_vars.items():
        monkeypatch.setenv(key, value)

    yield


@pytest.fixture
async def app() -> AsyncGenerator[Quart, None]:
    """Create a test Quart app instance."""
    # Import here to ensure environment variables are set first
    from app import app as quart_app

    quart_app.config["TESTING"] = True

    yield quart_app


@pytest.fixture
async def client(app: Quart):
    """Create a test client for the Quart app."""
    return app.test_client()


@pytest.fixture
def sample_product_dict():
    """Sample product data as dictionary."""
    return {
        "id": "CP-0001",
        "product_name": "Snow Veil",
        "description": "A soft, airy white with minimal undertones",
        "tags": "soft white, airy, minimal, clean",
        "price": 45.99,
        "sku": "CP-0001",
        "image_url": "https://test.blob.core.windows.net/images/snow-veil.jpg",
        "category": "Paint",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }


@pytest.fixture
def sample_product(sample_product_dict):
    """Sample product as Pydantic model."""
    from models import Product
    return Product(**sample_product_dict)


@pytest.fixture
def sample_creative_brief_dict():
    """Sample creative brief data as dictionary."""
    return {
        "overview": "Spring campaign for eco-friendly paint line",
        "objectives": "Increase brand awareness and drive 20% sales growth",
        "target_audience": "Homeowners aged 30-50, environmentally conscious",
        "key_message": "Beautiful colors that care for the planet",
        "tone_and_style": "Warm, optimistic, trustworthy",
        "deliverable": "Social media posts and email campaign",
        "timelines": "Launch March 1, run for 6 weeks",
        "visual_guidelines": "Natural lighting, green spaces, happy families",
        "cta": "Shop Now - Free Shipping"
    }


@pytest.fixture
def sample_creative_brief(sample_creative_brief_dict):
    """Sample creative brief as Pydantic model."""
    from models import CreativeBrief
    return CreativeBrief(**sample_creative_brief_dict)


@pytest.fixture
def authenticated_headers():
    """Headers simulating an authenticated user via EasyAuth."""
    return {
        "X-Ms-Client-Principal-Id": "test-user-123",
        "X-Ms-Client-Principal-Name": "test@example.com",
        "X-Ms-Client-Principal-Idp": "aad"
    }


@pytest.fixture
def admin_headers():
    """Headers with admin API key."""
    return {
        "X-Admin-API-Key": "test-admin-key"
    }


# =============================================================================
# Shared Mock Service Fixtures
# =============================================================================


@pytest.fixture
def fake_image_base64():
    """Base64-encoded fake image data for testing uploads."""
    import base64
    return base64.b64encode(b"fake-image-data").decode()


@pytest.fixture
def mock_cosmos_service_instance():
    """Pre-configured AsyncMock for CosmosDB service.

    Returns a mock with common methods pre-configured. Use in tests that
    need a Cosmos service mock without patching.
    """
    from unittest.mock import AsyncMock
    mock = AsyncMock()
    mock.add_message_to_conversation = AsyncMock()
    mock.get_conversation = AsyncMock(return_value=None)
    mock.upsert_conversation = AsyncMock()
    mock.get_all_products = AsyncMock(return_value=[])
    mock.get_product_by_sku = AsyncMock(return_value=None)
    mock.upsert_product = AsyncMock()
    mock.delete_product = AsyncMock(return_value=True)
    return mock


@pytest.fixture
def mock_blob_service_instance():
    """Pre-configured AsyncMock for Blob Storage service.

    Returns a mock with common attributes set up. Use in tests that need
    a blob service mock without patching.
    """
    from unittest.mock import AsyncMock, MagicMock
    mock = AsyncMock()
    mock.initialize = AsyncMock()

    # Set up container mocks
    mock_blob_client = AsyncMock()
    mock_blob_client.upload_blob = AsyncMock()
    mock_blob_client.url = "https://test.blob.core.windows.net/images/test.jpg"

    mock_container = MagicMock()
    mock_container.get_blob_client = MagicMock(return_value=mock_blob_client)

    mock._product_images_container = mock_container
    mock._generated_images_container = mock_container
    mock._mock_blob_client = mock_blob_client  # Expose for assertions

    return mock


@pytest.fixture
def mock_orchestrator_instance():
    """Pre-configured AsyncMock for ContentGenerationOrchestrator.

    Returns a mock with common methods pre-configured.
    """
    from unittest.mock import AsyncMock
    mock = AsyncMock()
    mock.parse_brief = AsyncMock()
    mock.generate_content_stream = AsyncMock()
    mock.process_message = AsyncMock()
    mock.initialize = AsyncMock()
    mock.confirm_brief = AsyncMock()
    return mock


def create_mock_process_message(responses):
    """Factory to create mock_process_message async generator.

    Args:
        responses: List of dicts to yield from the generator

    Returns:
        Async generator function suitable for mock_orchestrator.process_message

    Example:
        mock_orchestrator.process_message = create_mock_process_message([
            {"type": "message", "content": "Hello", "is_final": True}
        ])
    """
    async def mock_process_message(*_args, **_kwargs):
        for response in responses:
            yield response
    return mock_process_message


def create_mock_generate_content_stream(responses):
    """Factory to create mock_generate_content_stream async generator.

    Args:
        responses: List of dicts to yield from the generator

    Returns:
        Async generator function for mock_orchestrator.generate_content_stream
    """
    async def mock_generate_content_stream(*_args, **_kwargs):
        for response in responses:
            yield response
    return mock_generate_content_stream
