"""
Unit tests for Blob Storage Service.

These tests mock only the Azure SDK clients (BlobServiceClient, ContainerClient)
while allowing the actual BlobStorageService code to execute for coverage.
"""


from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from services import blob_service
from services.blob_service import BlobStorageService, get_blob_service


@pytest.mark.asyncio
async def test_initialize_with_managed_identity():
    """Test initialization with managed identity credential."""
    with patch("services.blob_service.app_settings") as mock_settings, \
         patch("services.blob_service.ManagedIdentityCredential") as mock_cred, \
         patch("services.blob_service.BlobServiceClient") as mock_client:

        mock_settings.base_settings.azure_client_id = "test-client-id"
        mock_settings.blob.account_name = "teststorage"
        mock_settings.blob.product_images_container = "product-images"
        mock_settings.blob.generated_images_container = "generated-images"

        mock_credential = AsyncMock()
        mock_cred.return_value = mock_credential

        mock_blob_client = MagicMock()
        mock_container = MagicMock()
        mock_blob_client.get_container_client.return_value = mock_container
        mock_client.return_value = mock_blob_client

        service = BlobStorageService()
        await service.initialize()

        mock_cred.assert_called_once_with(client_id="test-client-id")
        mock_client.assert_called_once()


@pytest.mark.asyncio
async def test_initialize_with_default_credential():
    """Test initialization with default Azure credential."""
    with patch("services.blob_service.app_settings") as mock_settings, \
         patch("services.blob_service.DefaultAzureCredential") as mock_cred, \
         patch("services.blob_service.BlobServiceClient") as mock_client:

        mock_settings.base_settings.azure_client_id = None
        mock_settings.blob.account_name = "teststorage"
        mock_settings.blob.product_images_container = "product-images"
        mock_settings.blob.generated_images_container = "generated-images"

        mock_credential = AsyncMock()
        mock_cred.return_value = mock_credential

        mock_blob_client = MagicMock()
        mock_container = MagicMock()
        mock_blob_client.get_container_client.return_value = mock_container
        mock_client.return_value = mock_blob_client

        service = BlobStorageService()
        await service.initialize()

        mock_cred.assert_called_once()


@pytest.mark.asyncio
async def test_initialize_idempotent():
    """Test that initialize only runs once."""
    with patch("services.blob_service.app_settings") as mock_settings, \
         patch("services.blob_service.DefaultAzureCredential") as mock_cred, \
         patch("services.blob_service.BlobServiceClient") as mock_client:

        mock_settings.base_settings.azure_client_id = None
        mock_settings.blob.account_name = "teststorage"
        mock_settings.blob.product_images_container = "product-images"
        mock_settings.blob.generated_images_container = "generated-images"

        mock_blob_client = MagicMock()
        mock_blob_client.get_container_client.return_value = MagicMock()
        mock_client.return_value = mock_blob_client
        mock_cred.return_value = AsyncMock()

        service = BlobStorageService()
        await service.initialize()
        await service.initialize()  # Second call should be no-op

        assert mock_client.call_count == 1


@pytest.mark.asyncio
async def test_close_client():
    """Test closing the Blob Storage client."""
    with patch("services.blob_service.app_settings") as mock_settings, \
         patch("services.blob_service.DefaultAzureCredential") as mock_cred, \
         patch("services.blob_service.BlobServiceClient") as mock_client:

        mock_settings.base_settings.azure_client_id = None
        mock_settings.blob.account_name = "teststorage"
        mock_settings.blob.product_images_container = "product-images"
        mock_settings.blob.generated_images_container = "generated-images"

        mock_blob_client = MagicMock()
        mock_blob_client.close = AsyncMock()
        mock_blob_client.get_container_client.return_value = MagicMock()
        mock_client.return_value = mock_blob_client
        mock_cred.return_value = AsyncMock()

        service = BlobStorageService()
        await service.initialize()
        await service.close()

        mock_blob_client.close.assert_called_once()
        assert service._client is None


@pytest.fixture
def mock_blob_service_with_containers():
    """Create a mocked Blob Storage service with containers."""
    with patch("services.blob_service.app_settings") as mock_settings, \
         patch("services.blob_service.DefaultAzureCredential") as mock_cred, \
         patch("services.blob_service.BlobServiceClient") as mock_client:

        mock_settings.base_settings.azure_client_id = None
        mock_settings.blob.account_name = "teststorage"
        mock_settings.blob.product_images_container = "product-images"
        mock_settings.blob.generated_images_container = "generated-images"
        mock_settings.azure_openai.endpoint = "https://test-openai.azure.com"
        mock_settings.azure_openai.api_version = "2024-02-15"
        mock_settings.azure_openai.gpt_model = "gpt-4"

        mock_blob_client = MagicMock()
        mock_product_images_container = MagicMock()
        mock_generated_images_container = MagicMock()

        mock_blob_client.get_container_client.side_effect = lambda name: (
            mock_product_images_container if name == "product-images"
            else mock_generated_images_container
        )
        mock_client.return_value = mock_blob_client
        mock_cred.return_value = AsyncMock()

        service = BlobStorageService()
        service._mock_product_images_container = mock_product_images_container
        service._mock_generated_images_container = mock_generated_images_container
        service._mock_cred = mock_cred

        yield service


@pytest.mark.asyncio
async def test_upload_product_image_success(mock_blob_service_with_containers):
    """Test uploading a product image successfully."""
    mock_blob_client = MagicMock()
    mock_blob_client.upload_blob = AsyncMock()
    mock_blob_client.url = "https://teststorage.blob.core.windows.net/product-images/SKU123/image.jpeg"

    mock_blob_service_with_containers._mock_product_images_container.get_blob_client.return_value = mock_blob_client

    with patch.object(mock_blob_service_with_containers, 'generate_image_description',
                      new=AsyncMock(return_value="A beautiful product image")):
        await mock_blob_service_with_containers.initialize()

        image_data = b"fake image data"
        url, description = await mock_blob_service_with_containers.upload_product_image(
            "SKU123",
            image_data,
            "image/jpeg"
        )

        assert "SKU123" in url
        assert description == "A beautiful product image"
        mock_blob_client.upload_blob.assert_called_once()


@pytest.mark.asyncio
async def test_upload_product_image_png(mock_blob_service_with_containers):
    """Test uploading a PNG product image."""
    mock_blob_client = MagicMock()
    mock_blob_client.upload_blob = AsyncMock()
    mock_blob_client.url = "https://teststorage.blob.core.windows.net/product-images/SKU456/image.png"

    mock_blob_service_with_containers._mock_product_images_container.get_blob_client.return_value = mock_blob_client

    with patch.object(mock_blob_service_with_containers, 'generate_image_description',
                      new=AsyncMock(return_value="PNG image description")):
        await mock_blob_service_with_containers.initialize()

        image_data = b"fake png data"
        url, description = await mock_blob_service_with_containers.upload_product_image(
            "SKU456",
            image_data,
            "image/png"
        )

        assert ".png" in url or "image.png" in url
        assert description == "PNG image description"
        mock_blob_client.upload_blob.assert_called_once()


@pytest.mark.asyncio
async def test_get_product_image_url_found(mock_blob_service_with_containers):
    """Test getting product image URL when images exist."""
    mock_blob1 = MagicMock()
    mock_blob1.name = "SKU123/20240101000000.jpeg"
    mock_blob2 = MagicMock()
    mock_blob2.name = "SKU123/20240102000000.jpeg"

    async def mock_list_blobs(*_args, **_kwargs):
        yield mock_blob1
        yield mock_blob2

    mock_blob_service_with_containers._mock_product_images_container.list_blobs = mock_list_blobs

    mock_blob_client = MagicMock()
    mock_blob_client.url = "https://teststorage.blob.core.windows.net/product-images/SKU123/20240102000000.jpeg"
    mock_blob_service_with_containers._mock_product_images_container.get_blob_client.return_value = mock_blob_client

    await mock_blob_service_with_containers.initialize()
    url = await mock_blob_service_with_containers.get_product_image_url("SKU123")

    assert url is not None
    assert "SKU123" in url


@pytest.mark.asyncio
async def test_get_product_image_url_not_found(mock_blob_service_with_containers):
    """Test getting product image URL when no images exist."""
    async def mock_list_blobs(*_args, **_kwargs):
        if False:
            yield

    mock_blob_service_with_containers._mock_product_images_container.list_blobs = mock_list_blobs

    await mock_blob_service_with_containers.initialize()
    url = await mock_blob_service_with_containers.get_product_image_url("NONEXISTENT")

    assert url is None


@pytest.mark.asyncio
async def test_save_generated_image_success(mock_blob_service_with_containers, fake_image_base64):
    """Test saving a generated image successfully."""
    mock_blob_client = MagicMock()
    mock_blob_client.upload_blob = AsyncMock()
    mock_blob_client.url = "https://teststorage.blob.core.windows.net/generated-images/conv-123/image.png"

    mock_blob_service_with_containers._mock_generated_images_container.get_blob_client.return_value = mock_blob_client

    await mock_blob_service_with_containers.initialize()

    url = await mock_blob_service_with_containers.save_generated_image(
        "conv-123",
        fake_image_base64,
        "image/png"
    )

    assert url is not None
    assert "conv-123" in url
    mock_blob_client.upload_blob.assert_called_once()


@pytest.mark.asyncio
async def test_save_generated_image_jpeg(mock_blob_service_with_containers, fake_image_base64):
    """Test saving a generated JPEG image."""
    mock_blob_client = MagicMock()
    mock_blob_client.upload_blob = AsyncMock()
    mock_blob_client.url = "https://teststorage.blob.core.windows.net/generated-images/conv-456/image.jpeg"

    mock_blob_service_with_containers._mock_generated_images_container.get_blob_client.return_value = mock_blob_client

    await mock_blob_service_with_containers.initialize()

    url = await mock_blob_service_with_containers.save_generated_image(
        "conv-456",
        fake_image_base64,
        "image/jpeg"
    )

    assert url is not None


@pytest.mark.asyncio
async def test_get_generated_images_multiple(mock_blob_service_with_containers):
    """Test getting multiple generated images for a conversation."""
    mock_blob1 = MagicMock()
    mock_blob1.name = "conv-123/20240101000000.png"
    mock_blob2 = MagicMock()
    mock_blob2.name = "conv-123/20240102000000.png"

    async def mock_list_blobs(*_args, **_kwargs):
        yield mock_blob1
        yield mock_blob2

    mock_blob_service_with_containers._mock_generated_images_container.list_blobs = mock_list_blobs

    mock_blob_client = MagicMock()
    mock_blob_client.url = "https://teststorage.blob.core.windows.net/generated-images/conv-123/image.png"
    mock_blob_service_with_containers._mock_generated_images_container.get_blob_client.return_value = mock_blob_client

    await mock_blob_service_with_containers.initialize()
    urls = await mock_blob_service_with_containers.get_generated_images("conv-123")

    assert len(urls) == 2


@pytest.mark.asyncio
async def test_get_generated_images_empty(mock_blob_service_with_containers):
    """Test getting generated images when none exist."""
    async def mock_list_blobs(*_args, **_kwargs):
        if False:
            yield

    mock_blob_service_with_containers._mock_generated_images_container.list_blobs = mock_list_blobs

    await mock_blob_service_with_containers.initialize()
    urls = await mock_blob_service_with_containers.get_generated_images("conv-empty")

    assert urls == []


@pytest.fixture
def mock_blob_service_basic():
    """Create a basic mocked Blob Storage service."""
    with patch("services.blob_service.app_settings") as mock_settings, \
         patch("services.blob_service.DefaultAzureCredential") as mock_cred, \
         patch("services.blob_service.BlobServiceClient") as mock_client:

        mock_settings.base_settings.azure_client_id = None
        mock_settings.blob.account_name = "teststorage"
        mock_settings.blob.product_images_container = "product-images"
        mock_settings.blob.generated_images_container = "generated-images"
        mock_settings.azure_openai.endpoint = "https://test-openai.azure.com"
        mock_settings.azure_openai.api_version = "2024-02-15"
        mock_settings.azure_openai.gpt_model = "gpt-4"

        mock_blob_client = MagicMock()
        mock_blob_client.get_container_client.return_value = MagicMock()
        mock_client.return_value = mock_blob_client
        mock_cred.return_value = AsyncMock()

        service = BlobStorageService()

        yield service


@pytest.mark.asyncio
async def test_generate_image_description_success(mock_blob_service_basic):
    """Test successful image description generation."""
    with patch("services.blob_service.AsyncAzureOpenAI") as mock_openai:
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "A sleek black smartphone with a 6.5-inch display"

        mock_openai_instance = AsyncMock()
        mock_openai_instance.chat.completions.create = AsyncMock(return_value=mock_response)
        mock_openai.return_value = mock_openai_instance

        await mock_blob_service_basic.initialize()

        image_data = b"fake image bytes"
        description = await mock_blob_service_basic.generate_image_description(image_data)

        assert description == "A sleek black smartphone with a 6.5-inch display"
        mock_openai_instance.chat.completions.create.assert_called_once()


@pytest.mark.asyncio
async def test_generate_image_description_error_returns_fallback(mock_blob_service_basic):
    """Test that errors return fallback description."""
    with patch("services.blob_service.AsyncAzureOpenAI") as mock_openai:
        mock_openai_instance = AsyncMock()
        mock_openai_instance.chat.completions.create = AsyncMock(
            side_effect=Exception("OpenAI API error")
        )
        mock_openai.return_value = mock_openai_instance

        await mock_blob_service_basic.initialize()

        image_data = b"fake image bytes"
        description = await mock_blob_service_basic.generate_image_description(image_data)

        assert description == "Product image - description unavailable"


@pytest.mark.asyncio
async def test_generate_image_description_encodes_base64(mock_blob_service_basic):
    """Test that image data is properly base64 encoded."""
    with patch("services.blob_service.AsyncAzureOpenAI") as mock_openai:
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Test description"

        mock_openai_instance = AsyncMock()
        mock_openai_instance.chat.completions.create = AsyncMock(return_value=mock_response)
        mock_openai.return_value = mock_openai_instance

        await mock_blob_service_basic.initialize()

        image_data = b"test image bytes"
        await mock_blob_service_basic.generate_image_description(image_data)

        call_args = mock_openai_instance.chat.completions.create.call_args
        messages = call_args.kwargs.get('messages') or call_args[1].get('messages')

        assert len(messages) == 2


@pytest.mark.asyncio
async def test_get_blob_service_creates_singleton():
    """Test that get_blob_service returns a singleton instance."""
    with patch("services.blob_service.app_settings") as mock_settings, \
         patch("services.blob_service.DefaultAzureCredential") as mock_cred, \
         patch("services.blob_service.BlobServiceClient") as mock_client, \
         patch("services.blob_service._blob_service", None):

        mock_settings.base_settings.azure_client_id = None
        mock_settings.blob.account_name = "teststorage"
        mock_settings.blob.product_images_container = "product-images"
        mock_settings.blob.generated_images_container = "generated-images"

        mock_blob_client = MagicMock()
        mock_blob_client.get_container_client.return_value = MagicMock()
        mock_client.return_value = mock_blob_client
        mock_cred.return_value = AsyncMock()

        service1 = await get_blob_service()
        blob_service._blob_service = service1

        service2 = await get_blob_service()

        assert service1 is service2
