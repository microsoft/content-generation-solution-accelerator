from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from services.search_service import SearchService, get_search_service


@pytest.fixture
def mock_search_service():
    """Create a mocked search service for search client tests."""
    with patch("services.search_service.app_settings") as mock_settings, \
         patch("services.search_service.DefaultAzureCredential") as mock_cred, \
         patch("services.search_service.SearchClient") as mock_search_client:

        mock_settings.search.endpoint = "https://test.search.windows.net"
        mock_settings.search.products_index = "products-index"
        mock_settings.search.images_index = "images-index"
        mock_settings.search.admin_key = None

        mock_cred.return_value = MagicMock()

        mock_client = MagicMock()
        mock_search_client.return_value = mock_client

        service = SearchService()
        service._mock_client = mock_client
        service._images_client = mock_client

        yield service


def test_get_credential_rbac_success():
    """Test getting credential via RBAC."""
    with patch("services.search_service.app_settings") as mock_settings, \
         patch("services.search_service.DefaultAzureCredential") as mock_cred:

        mock_settings.search.endpoint = "https://test.search.windows.net"
        mock_settings.search.admin_key = None

        mock_credential = MagicMock()
        mock_cred.return_value = mock_credential

        service = SearchService()
        cred = service._get_credential()

        assert cred is not None
        mock_cred.assert_called_once()


def test_get_credential_api_key_fallback():
    """Test fallback to API key when RBAC fails."""
    with patch("services.search_service.app_settings") as mock_settings, \
         patch("services.search_service.DefaultAzureCredential") as mock_cred, \
         patch("services.search_service.AzureKeyCredential") as mock_key_cred:

        mock_settings.search.endpoint = "https://test.search.windows.net"
        mock_settings.search.admin_key = "test-api-key"

        # RBAC fails
        mock_cred.side_effect = Exception("RBAC failed")

        mock_key_credential = MagicMock()
        mock_key_cred.return_value = mock_key_credential

        service = SearchService()
        cred = service._get_credential()

        assert cred is not None
        mock_key_cred.assert_called_once_with("test-api-key")


def test_get_credential_cached():
    """Test that credential is cached after first retrieval."""
    with patch("services.search_service.app_settings") as mock_settings, \
         patch("services.search_service.DefaultAzureCredential") as mock_cred:

        mock_settings.search.endpoint = "https://test.search.windows.net"

        mock_credential = MagicMock()
        mock_cred.return_value = mock_credential

        service = SearchService()

        cred1 = service._get_credential()
        cred2 = service._get_credential()

        assert cred1 is cred2
        assert mock_cred.call_count == 1  # Only called once


def test_get_products_client_creates_once():
    """Test that products client is created only once."""
    with patch("services.search_service.app_settings") as mock_settings, \
         patch("services.search_service.DefaultAzureCredential") as mock_cred, \
         patch("services.search_service.SearchClient") as mock_search_client:

        mock_settings.search.endpoint = "https://test.search.windows.net"
        mock_settings.search.products_index = "products-index"
        mock_settings.search.admin_key = None

        mock_cred.return_value = MagicMock()
        mock_search_client.return_value = MagicMock()

        service = SearchService()

        client1 = service._get_products_client()
        client2 = service._get_products_client()

        assert client1 is client2
        assert mock_search_client.call_count == 1


def test_get_images_client_creates_once():
    """Test that images client is created only once."""
    with patch("services.search_service.app_settings") as mock_settings, \
         patch("services.search_service.DefaultAzureCredential") as mock_cred, \
         patch("services.search_service.SearchClient") as mock_search_client:

        mock_settings.search.endpoint = "https://test.search.windows.net"
        mock_settings.search.images_index = "images-index"
        mock_settings.search.admin_key = None

        mock_cred.return_value = MagicMock()
        mock_search_client.return_value = MagicMock()

        service = SearchService()

        client1 = service._get_images_client()
        client2 = service._get_images_client()

        assert client1 is client2
        assert mock_search_client.call_count == 1


def test_get_products_client_raises_without_endpoint():
    """Test error when endpoint is not configured."""
    with patch("services.search_service.app_settings") as mock_settings:
        mock_settings.search = None

        service = SearchService()

        with pytest.raises(ValueError, match="endpoint not configured"):
            service._get_products_client()


def test_get_images_client_raises_without_endpoint():
    """Test error when images client endpoint is not configured."""
    with patch("services.search_service.app_settings") as mock_settings:
        mock_settings.search = None

        service = SearchService()

        with pytest.raises(ValueError, match="endpoint not configured"):
            service._get_images_client()


def test_get_credential_no_credentials():
    """Test error when no credentials are available."""
    with patch("services.search_service.app_settings") as mock_settings, \
         patch("services.search_service.DefaultAzureCredential") as mock_cred:

        mock_settings.search = MagicMock()
        mock_settings.search.admin_key = None

        # Make RBAC fail
        mock_cred.side_effect = Exception("No credentials")

        service = SearchService()

        with pytest.raises(ValueError, match="No valid search credentials available"):
            service._get_credential()


@pytest.mark.asyncio
async def test_search_products_basic(mock_search_service):
    """Test basic product search."""
    mock_results = [
        {
            "id": "prod-1",
            "product_name": "Premium Paint",
            "sku": "PAINT-001",
            "model": "Premium",
            "category": "Interior",
            "sub_category": "Paint",
            "marketing_description": "High quality paint",
            "detailed_spec_description": "Coverage: 400 sq ft/gallon",
            "image_description": "Blue paint can",
            "@search.score": 0.95
        }
    ]

    mock_search_service._mock_client.search.return_value = mock_results

    results = await mock_search_service.search_products("paint")

    assert len(results) == 1
    assert results[0]["product_name"] == "Premium Paint"
    assert results[0]["search_score"] == 0.95


@pytest.mark.asyncio
async def test_search_products_with_category_filter(mock_search_service):
    """Test product search with category filter."""
    mock_results = []
    mock_search_service._mock_client.search.return_value = mock_results

    await mock_search_service.search_products("paint", category="Interior")

    # Verify filter was passed
    call_args = mock_search_service._mock_client.search.call_args
    assert "category eq 'Interior'" in str(call_args)


@pytest.mark.asyncio
async def test_search_products_with_subcategory_filter(mock_search_service):
    """Test product search with sub-category filter."""
    mock_results = []
    mock_search_service._mock_client.search.return_value = mock_results

    await mock_search_service.search_products("paint", category="Interior", sub_category="Paint")

    call_args = mock_search_service._mock_client.search.call_args
    filter_str = call_args[1].get('filter', '')
    assert "sub_category eq 'Paint'" in filter_str


@pytest.mark.asyncio
async def test_search_products_error_returns_empty(mock_search_service):
    """Test that search errors return empty list."""
    mock_search_service._mock_client.search.side_effect = Exception("Search failed")

    results = await mock_search_service.search_products("paint")

    assert results == []


@pytest.mark.asyncio
async def test_search_products_custom_top(mock_search_service):
    """Test product search with custom top parameter."""
    mock_results = []
    mock_search_service._mock_client.search.return_value = mock_results

    await mock_search_service.search_products("paint", top=10)

    call_args = mock_search_service._mock_client.search.call_args
    assert call_args[1].get('top') == 10


@pytest.mark.asyncio
async def test_search_images_basic(mock_search_service):
    """Test basic image search."""
    mock_results = [
        {
            "id": "img-1",
            "name": "Ocean Blue",
            "filename": "ocean_blue.png",
            "primary_color": "#003366",
            "secondary_color": "#4499CC",
            "color_family": "Cool",
            "mood": "Calm",
            "style": "Modern",
            "description": "Calming ocean blue",
            "use_cases": "Living rooms, bedrooms",
            "blob_url": "https://storage.blob.core.windows.net/images/ocean_blue.png",
            "keywords": ["blue", "ocean", "calm"],
            "@search.score": 0.88
        }
    ]

    mock_search_service._mock_client.search.return_value = mock_results

    results = await mock_search_service.search_images("blue")

    assert len(results) == 1
    assert results[0]["name"] == "Ocean Blue"
    assert results[0]["color_family"] == "Cool"


@pytest.mark.asyncio
async def test_search_images_with_color_family_filter(mock_search_service):
    """Test image search with color family filter."""
    mock_results = []
    mock_search_service._mock_client.search.return_value = mock_results

    await mock_search_service.search_images("blue", color_family="Cool")

    call_args = mock_search_service._mock_client.search.call_args
    filter_str = call_args[1].get('filter', '')
    assert "color_family eq 'Cool'" in filter_str


@pytest.mark.asyncio
async def test_search_images_error_returns_empty(mock_search_service):
    """Test that search errors return empty list."""
    mock_search_service._mock_client.search.side_effect = Exception("Search failed")

    results = await mock_search_service.search_images("blue")

    assert results == []


@pytest.mark.asyncio
async def test_get_grounding_context_products_only(mock_search_service):
    """Test grounding context with products only."""
    with patch.object(
        mock_search_service, 'search_products',
        new=AsyncMock(return_value=[{"product_name": "Test Paint", "sku": "PAINT-001"}])
    ), patch.object(
        mock_search_service, 'search_images', new=AsyncMock(return_value=[])
    ):

        context = await mock_search_service.get_grounding_context("paint")

        assert context["product_count"] == 1
        assert context["image_count"] == 0
        assert len(context["products"]) == 1


@pytest.mark.asyncio
async def test_get_grounding_context_with_images(mock_search_service):
    """Test grounding context with products and images."""
    with patch.object(
        mock_search_service, 'search_products',
        new=AsyncMock(return_value=[{"product_name": "Test Paint", "sku": "PAINT-001"}])
    ), patch.object(
        mock_search_service, 'search_images',
        new=AsyncMock(return_value=[{"name": "Ocean Blue", "mood": "Calm"}])
    ):

        context = await mock_search_service.get_grounding_context(
            product_query="paint",
            image_query="blue"
        )

        assert context["product_count"] == 1
        assert context["image_count"] == 1
        assert "grounding_summary" in context


@pytest.mark.asyncio
async def test_get_grounding_context_with_filters(mock_search_service):
    """Test grounding context with category filter."""
    with patch.object(mock_search_service, 'search_products', new=AsyncMock(return_value=[])) as mock_search:
        _ = await mock_search_service.get_grounding_context(
            product_query="paint",
            category="Interior"
        )

        mock_search.assert_called_once_with(
            query="paint",
            category="Interior",
            top=5
        )


def test_build_summary_with_products():
    """Test building summary with product data."""
    with patch("services.search_service.app_settings") as mock_settings:
        mock_settings.search = None
        service = SearchService()

        products = [
            {
                "product_name": "Premium Paint",
                "sku": "PAINT-001",
                "category": "Interior",
                "sub_category": "Paint",
                "marketing_description": "High quality interior paint for all surfaces",
                "image_description": "Blue paint can with metal handle"
            }
        ]

        summary = service._build_grounding_summary(products, [])

        assert "Premium Paint" in summary
        assert "PAINT-001" in summary
        assert "Interior" in summary


def test_build_summary_with_images():
    """Test building summary with image data."""
    with patch("services.search_service.app_settings") as mock_settings:
        mock_settings.search = None
        service = SearchService()

        images = [
            {
                "name": "Ocean Blue",
                "primary_color": "#003366",
                "secondary_color": "#4499CC",
                "mood": "Calm",
                "style": "Modern",
                "use_cases": "Living rooms, bedrooms"
            }
        ]

        summary = service._build_grounding_summary([], images)

        assert "Ocean Blue" in summary
        assert "Calm" in summary
        assert "Modern" in summary


def test_build_summary_empty_inputs():
    """Test building summary with empty inputs."""
    with patch("services.search_service.app_settings") as mock_settings:
        mock_settings.search = None
        service = SearchService()

        summary = service._build_grounding_summary([], [])

        assert summary == ""


@pytest.mark.asyncio
async def test_get_search_service_returns_singleton():
    """Test that get_search_service returns a singleton."""
    with patch("services.search_service._search_service", None):
        # Reset global
        import services.search_service as module
        module._search_service = None

        service1 = await get_search_service()
        module._search_service = service1  # Set for next call
        service2 = await get_search_service()

        assert service1 is service2
        assert isinstance(service1, SearchService)
