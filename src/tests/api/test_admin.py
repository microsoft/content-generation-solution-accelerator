from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from models import Product


@pytest.mark.asyncio
async def test_upload_images_without_api_key(client, fake_image_base64):
    """Test upload images endpoint without API key (should be allowed in dev)."""
    with patch("api.admin.get_blob_service") as mock_blob:
        mock_blob_service = AsyncMock()
        mock_blob_service.initialize = AsyncMock()
        mock_container = AsyncMock()
        mock_blob_client = AsyncMock()
        mock_blob_client.upload_blob = AsyncMock()
        mock_blob_client.url = "https://test.blob/image.jpg"
        mock_container.get_blob_client = MagicMock(return_value=mock_blob_client)
        mock_blob_service._product_images_container = mock_container
        mock_blob.return_value = mock_blob_service

        response = await client.post(
            "/api/admin/upload-images",
            json={
                "images": [
                    {
                        "filename": "test.jpg",
                        "content_type": "image/jpeg",
                        "data": fake_image_base64
                    }
                ]
            }
        )

        assert response.status_code == 200


@pytest.mark.asyncio
async def test_upload_images_with_invalid_api_key(client):
    """Test upload images endpoint with invalid API key returns 401."""
    with patch("api.admin.ADMIN_API_KEY", "correct-key"):
        response = await client.post(
            "/api/admin/upload-images",
            headers={"X-Admin-API-Key": "wrong-key"},
            json={
                "images": [{"filename": "test.jpg", "data": "base64data"}]
            }
        )

        assert response.status_code == 401
        data = await response.get_json()
        assert "Unauthorized" in data.get("error", "")


@pytest.mark.asyncio
async def test_load_sample_data_unauthorized(client):
    """Test load sample data endpoint with invalid API key returns 401."""
    with patch("api.admin.ADMIN_API_KEY", "correct-key"):
        response = await client.post(
            "/api/admin/load-sample-data",
            headers={"X-Admin-API-Key": "wrong-key"},
            json={"products": []}
        )

        assert response.status_code == 401


@pytest.mark.asyncio
async def test_create_search_index_unauthorized(client):
    """Test create search index endpoint with invalid API key returns 401."""
    with patch("api.admin.ADMIN_API_KEY", "correct-key"):
        response = await client.post(
            "/api/admin/create-search-index",
            headers={"X-Admin-API-Key": "wrong-key"}
        )

        assert response.status_code == 401


@pytest.mark.asyncio
async def test_upload_images_with_valid_api_key(client, admin_headers, fake_image_base64):
    """Test upload images with valid API key."""
    with patch("api.admin.get_blob_service") as mock_blob, \
         patch("api.admin.ADMIN_API_KEY", "test-admin-key"):

        mock_blob_service = AsyncMock()
        mock_blob_service.initialize = AsyncMock()
        mock_container = AsyncMock()
        mock_blob_client = AsyncMock()
        mock_blob_client.upload_blob = AsyncMock()
        mock_blob_client.url = "https://test.blob/image.jpg"
        mock_container.get_blob_client = MagicMock(return_value=mock_blob_client)
        mock_blob_service._product_images_container = mock_container
        mock_blob.return_value = mock_blob_service

        response = await client.post(
            "/api/admin/upload-images",
            headers=admin_headers,
            json={
                "images": [
                    {
                        "filename": "test.jpg",
                        "content_type": "image/jpeg",
                        "data": fake_image_base64
                    }
                ]
            }
        )

        assert response.status_code == 200


@pytest.mark.asyncio
async def test_upload_images_success(client, fake_image_base64):
    """Test successful image upload."""
    with patch("api.admin.get_blob_service") as mock_blob:
        mock_blob_service = AsyncMock()
        mock_blob_service.initialize = AsyncMock()

        mock_blob_client = AsyncMock()
        mock_blob_client.upload_blob = AsyncMock()
        mock_blob_client.url = "https://test.blob/test.jpg"

        mock_container = AsyncMock()
        mock_container.get_blob_client = MagicMock(return_value=mock_blob_client)
        mock_blob_service._product_images_container = mock_container

        mock_blob.return_value = mock_blob_service

        response = await client.post(
            "/api/admin/upload-images",
            json={
                "images": [
                    {
                        "filename": "test.jpg",
                        "content_type": "image/jpeg",
                        "data": fake_image_base64
                    }
                ]
            }
        )

        assert response.status_code == 200
        data = await response.get_json()
        assert data["success"] is True
        assert data["uploaded"] == 1
        assert data["failed"] == 0
        assert len(data["results"]) == 1


@pytest.mark.asyncio
async def test_upload_images_multiple(client, fake_image_base64):
    """Test uploading multiple images."""
    with patch("api.admin.get_blob_service") as mock_blob:
        mock_blob_service = AsyncMock()
        mock_blob_service.initialize = AsyncMock()

        mock_blob_client = AsyncMock()
        mock_blob_client.upload_blob = AsyncMock()
        mock_blob_client.url = "https://test.blob/image.jpg"

        mock_container = AsyncMock()
        mock_container.get_blob_client = MagicMock(return_value=mock_blob_client)
        mock_blob_service._product_images_container = mock_container

        mock_blob.return_value = mock_blob_service

        response = await client.post(
            "/api/admin/upload-images",
            json={
                "images": [
                    {
                        "filename": "image1.jpg",
                        "content_type": "image/jpeg",
                        "data": fake_image_base64
                    },
                    {
                        "filename": "image2.png",
                        "content_type": "image/png",
                        "data": fake_image_base64
                    }
                ]
            }
        )

        assert response.status_code == 200
        data = await response.get_json()
        assert data["uploaded"] == 2
        assert len(data["results"]) == 2


@pytest.mark.asyncio
async def test_upload_images_missing_data(client):
    """Test upload with missing image data."""
    with patch("api.admin.get_blob_service") as mock_blob:
        mock_blob_service = AsyncMock()
        mock_blob_service.initialize = AsyncMock()
        mock_blob.return_value = mock_blob_service

        response = await client.post(
            "/api/admin/upload-images",
            json={
                "images": [
                    {
                        "filename": "test.jpg"
                        # Missing 'data' field
                    }
                ]
            }
        )

        assert response.status_code == 200
        data = await response.get_json()
        assert data["failed"] == 1
        assert data["uploaded"] == 0


@pytest.mark.asyncio
async def test_upload_images_no_images(client):
    """Test upload with empty images array."""
    response = await client.post(
        "/api/admin/upload-images",
        json={"images": []}
    )

    assert response.status_code == 400
    data = await response.get_json()
    assert "error" in data


@pytest.mark.asyncio
async def test_upload_images_invalid_base64(client):
    """Test upload with invalid base64 data."""
    with patch("api.admin.get_blob_service") as mock_blob:
        mock_blob_service = AsyncMock()
        mock_blob_service.initialize = AsyncMock()
        mock_blob.return_value = mock_blob_service

        response = await client.post(
            "/api/admin/upload-images",
            json={
                "images": [
                    {
                        "filename": "test.jpg",
                        "content_type": "image/jpeg",
                        "data": "not-valid-base64!@#"
                    }
                ]
            }
        )

        assert response.status_code == 200
        data = await response.get_json()
        assert data["failed"] == 1


@pytest.mark.asyncio
async def test_upload_images_blob_error(client, fake_image_base64):
    """Test upload when blob service fails."""
    with patch("api.admin.get_blob_service") as mock_blob:
        mock_blob_service = AsyncMock()
        mock_blob_service.initialize = AsyncMock()

        mock_blob_client = AsyncMock()
        mock_blob_client.upload_blob = AsyncMock(
            side_effect=Exception("Blob upload failed")
        )

        mock_container = AsyncMock()
        mock_container.get_blob_client = MagicMock(return_value=mock_blob_client)
        mock_blob_service._product_images_container = mock_container

        mock_blob.return_value = mock_blob_service

        response = await client.post(
            "/api/admin/upload-images",
            json={
                "images": [
                    {
                        "filename": "test.jpg",
                        "content_type": "image/jpeg",
                        "data": fake_image_base64
                    }
                ]
            }
        )

        assert response.status_code == 200
        data = await response.get_json()
        assert data["failed"] == 1


@pytest.mark.asyncio
async def test_upload_images_internal_server_error(client, fake_image_base64):
    """Test upload_images returns 500 when outer exception occurs."""
    with patch("api.admin.get_blob_service") as mock_blob:
        mock_blob_service = AsyncMock()
        mock_blob_service.initialize = AsyncMock(
            side_effect=Exception("Connection timeout to blob storage")
        )
        mock_blob.return_value = mock_blob_service

        response = await client.post(
            "/api/admin/upload-images",
            json={
                "images": [
                    {
                        "filename": "test.jpg",
                        "content_type": "image/jpeg",
                        "data": fake_image_base64
                    }
                ]
            }
        )

        assert response.status_code == 500
        data = await response.get_json()
        assert "error" in data
        assert "Internal server error" in data["error"]


@pytest.mark.asyncio
async def test_load_sample_data_success(client, sample_product_dict):
    """Test successful sample data loading."""
    with patch("api.admin.get_cosmos_service") as mock_cosmos:
        mock_cosmos_service = AsyncMock()
        mock_cosmos_service.upsert_product = AsyncMock(
            return_value=Product(**sample_product_dict)
        )
        mock_cosmos.return_value = mock_cosmos_service

        response = await client.post(
            "/api/admin/load-sample-data",
            json={
                "products": [sample_product_dict]
            }
        )

        assert response.status_code == 200
        data = await response.get_json()
        assert data["success"] is True
        assert data["loaded"] == 1
        assert data["failed"] == 0


@pytest.mark.asyncio
async def test_load_sample_data_multiple(client, sample_product_dict):
    """Test loading multiple products."""
    with patch("api.admin.get_cosmos_service") as mock_cosmos:
        mock_cosmos_service = AsyncMock()
        mock_cosmos_service.upsert_product = AsyncMock()
        mock_cosmos.return_value = mock_cosmos_service

        products = [
            {**sample_product_dict, "sku": "CP-0001"},
            {**sample_product_dict, "sku": "CP-0002"},
            {**sample_product_dict, "sku": "CP-0003"}
        ]

        response = await client.post(
            "/api/admin/load-sample-data",
            json={"products": products}
        )

        assert response.status_code == 200
        data = await response.get_json()
        assert data["loaded"] == 3


@pytest.mark.asyncio
async def test_load_sample_data_clear_existing(client, sample_product_dict):
    """Test loading with clear_existing flag."""
    with patch("api.admin.get_cosmos_service") as mock_cosmos:
        mock_cosmos_service = AsyncMock()
        mock_cosmos_service.delete_all_products = AsyncMock(return_value=5)
        mock_cosmos_service.upsert_product = AsyncMock()
        mock_cosmos.return_value = mock_cosmos_service

        response = await client.post(
            "/api/admin/load-sample-data",
            json={
                "products": [sample_product_dict],
                "clear_existing": True
            }
        )

        assert response.status_code == 200
        data = await response.get_json()
        assert data["deleted"] == 5
        assert data["loaded"] == 1


@pytest.mark.asyncio
async def test_load_sample_data_no_products(client):
    """Test loading with no products."""
    response = await client.post(
        "/api/admin/load-sample-data",
        json={"products": []}
    )

    assert response.status_code == 400
    data = await response.get_json()
    assert "error" in data


@pytest.mark.asyncio
async def test_load_sample_data_invalid_product(client):
    """Test loading with invalid product data."""
    with patch("api.admin.get_cosmos_service") as mock_cosmos:
        mock_cosmos_service = AsyncMock()
        mock_cosmos_service.upsert_product = AsyncMock(
            side_effect=Exception("Invalid product")
        )
        mock_cosmos.return_value = mock_cosmos_service

        response = await client.post(
            "/api/admin/load-sample-data",
            json={
                "products": [
                    {
                        "sku": "INVALID",
                        "product_name": "Test"
                    }
                ]
            }
        )

        assert response.status_code == 200
        data = await response.get_json()
        assert data["failed"] == 1


@pytest.mark.asyncio
async def test_load_sample_data_partial_failure(client, sample_product_dict):
    """Test loading with some products failing."""
    with patch("api.admin.get_cosmos_service") as mock_cosmos:
        mock_cosmos_service = AsyncMock()

        call_count = 0

        def side_effect(product):
            nonlocal call_count
            call_count += 1
            if call_count == 2:
                raise Exception("Cosmos error")
            return product

        mock_cosmos_service.upsert_product = AsyncMock(side_effect=side_effect)
        mock_cosmos.return_value = mock_cosmos_service

        products = [
            {**sample_product_dict, "sku": "CP-0001"},
            {**sample_product_dict, "sku": "CP-0002"}
        ]

        response = await client.post(
            "/api/admin/load-sample-data",
            json={"products": products}
        )

        assert response.status_code == 200
        data = await response.get_json()
        assert data["loaded"] == 1
        assert data["failed"] == 1
        assert data["success"] is False


@pytest.mark.asyncio
async def test_load_sample_data_internal_server_error(client, sample_product_dict):
    """Test load_sample_data returns 500 when outer exception occurs."""
    with patch("api.admin.get_cosmos_service") as mock_cosmos:
        mock_cosmos.side_effect = Exception("Failed to connect to Cosmos DB")

        response = await client.post(
            "/api/admin/load-sample-data",
            json={"products": [sample_product_dict]}
        )

        assert response.status_code == 500
        data = await response.get_json()
        assert "error" in data
        assert "Internal server error" in data["error"]


@pytest.mark.asyncio
async def test_create_search_index_success(client, sample_product):
    """Test successful search index creation."""
    with patch("api.admin.get_cosmos_service") as mock_cosmos, \
         patch("api.admin.app_settings") as mock_settings, \
         patch("azure.search.documents.indexes.SearchIndexClient") as mock_search_client, \
         patch("azure.search.documents.SearchClient") as mock_search:

        mock_settings.search = MagicMock()
        mock_settings.search.endpoint = "https://test-search.search.windows.net"
        mock_settings.search.products_index = "test-index"
        mock_settings.search.admin_key = "test-key"

        mock_cosmos_service = AsyncMock()
        mock_cosmos_service.get_all_products = AsyncMock(
            return_value=[sample_product]
        )
        mock_cosmos.return_value = mock_cosmos_service

        mock_search_instance = MagicMock()
        mock_search_instance.create_or_update_index = MagicMock()
        mock_search_instance.close = MagicMock()
        mock_search_client.return_value = mock_search_instance

        mock_search_upload_instance = MagicMock()
        mock_search_upload_instance.upload_documents = MagicMock(
            return_value=MagicMock(succeeded=[sample_product.sku])
        )
        mock_search_upload_instance.close = MagicMock()
        mock_search.return_value = mock_search_upload_instance

        response = await client.post("/api/admin/create-search-index")

        assert response.status_code == 200
        data = await response.get_json()
        assert data["success"] is True


@pytest.mark.asyncio
async def test_create_search_index_no_products(client):
    """Test index creation with no products."""
    with patch("api.admin.get_cosmos_service") as mock_cosmos, \
         patch("api.admin.app_settings") as mock_settings, \
         patch("azure.search.documents.indexes.SearchIndexClient") as mock_search_client, \
         patch("azure.search.documents.SearchClient") as mock_search:

        mock_settings.search.endpoint = "https://test-search.search.windows.net"
        mock_settings.search.products_index = "test-index"
        mock_settings.search.admin_key = "test-key"

        mock_cosmos_service = AsyncMock()
        mock_cosmos_service.get_all_products = AsyncMock(return_value=[])
        mock_cosmos.return_value = mock_cosmos_service

        mock_search_instance = MagicMock()
        mock_search_instance.create_or_update_index = MagicMock()
        mock_search_instance.close = MagicMock()
        mock_search_client.return_value = mock_search_instance

        mock_search_upload_instance = MagicMock()
        mock_search_upload_instance.close = MagicMock()
        mock_search.return_value = mock_search_upload_instance

        response = await client.post("/api/admin/create-search-index")

        assert response.status_code == 200


@pytest.mark.asyncio
async def test_create_search_index_search_not_configured(client):
    """Test create_search_index returns 500 when search endpoint not configured."""
    with patch("api.admin.app_settings") as mock_settings:
        mock_settings.search = MagicMock()
        mock_settings.search.endpoint = None

        response = await client.post("/api/admin/create-search-index")

        assert response.status_code == 500
        data = await response.get_json()
        assert "error" in data
        assert "Search service not configured" in data["error"]


@pytest.mark.asyncio
async def test_create_search_index_with_no_search_settings(client):
    """Test create_search_index returns 500 when search settings object is None."""
    with patch("api.admin.app_settings") as mock_settings:
        mock_settings.search = None

        response = await client.post("/api/admin/create-search-index")

        assert response.status_code == 500
        data = await response.get_json()
        assert "error" in data
        assert "Search service not configured" in data["error"]


@pytest.mark.asyncio
async def test_create_search_index_document_indexing_internal_error(client, sample_product):
    """Test create_search_index returns 500 when document indexing fails completely."""
    with patch("api.admin.get_cosmos_service") as mock_cosmos, \
         patch("api.admin.app_settings") as mock_settings, \
         patch("azure.search.documents.indexes.SearchIndexClient") as mock_search_client, \
         patch("azure.search.documents.SearchClient") as mock_search:

        mock_settings.search = MagicMock()
        mock_settings.search.endpoint = "https://test-search.search.windows.net"
        mock_settings.search.products_index = "test-index"
        mock_settings.search.admin_key = "test-key"

        mock_cosmos_service = AsyncMock()
        mock_cosmos_service.get_all_products = AsyncMock(
            return_value=[sample_product]
        )
        mock_cosmos.return_value = mock_cosmos_service

        mock_search_instance = MagicMock()
        mock_search_instance.create_or_update_index = MagicMock()
        mock_search_instance.close = MagicMock()
        mock_search_client.return_value = mock_search_instance

        mock_search_upload_instance = MagicMock()
        mock_search_upload_instance.upload_documents = MagicMock(
            side_effect=Exception("Service unavailable")
        )
        mock_search_upload_instance.close = MagicMock()
        mock_search.return_value = mock_search_upload_instance

        response = await client.post("/api/admin/create-search-index")

        assert response.status_code == 500
        data = await response.get_json()
        assert "error" in data
        assert "Failed to index documents" in data["error"] or "Internal server error" in data["error"]


@pytest.mark.asyncio
async def test_full_data_loading_workflow(client, sample_product_dict, fake_image_base64):
    """Test complete workflow: upload images -> load data -> create index."""
    # Step 1: Upload images
    with patch("api.admin.get_blob_service") as mock_blob:
        mock_blob_service = AsyncMock()
        mock_blob_service.initialize = AsyncMock()

        mock_blob_client = AsyncMock()
        mock_blob_client.upload_blob = AsyncMock()
        mock_blob_client.url = "https://test.blob/test.jpg"

        mock_container = AsyncMock()
        mock_container.get_blob_client = MagicMock(return_value=mock_blob_client)
        mock_blob_service._product_images_container = mock_container

        mock_blob.return_value = mock_blob_service

        response1 = await client.post(
            "/api/admin/upload-images",
            json={
                "images": [{
                    "filename": "test.jpg",
                    "content_type": "image/jpeg",
                    "data": fake_image_base64
                }]
            }
        )

        assert response1.status_code == 200

    # Step 2: Load sample data
    with patch("api.admin.get_cosmos_service") as mock_cosmos:
        mock_cosmos_service = AsyncMock()
        mock_cosmos_service.upsert_product = AsyncMock()
        mock_cosmos.return_value = mock_cosmos_service

        response2 = await client.post(
            "/api/admin/load-sample-data",
            json={"products": [sample_product_dict]}
        )

        assert response2.status_code == 200
        data2 = await response2.get_json()
        assert data2["loaded"] == 1


@pytest.mark.asyncio
async def test_create_search_index_missing_endpoint(client):
    """Test create search index fails without search endpoint."""
    with patch("api.admin.app_settings") as mock_settings:
        mock_settings.search = None

        response = await client.post(
            "/api/admin/create-search-index",
            json={"index_name": "test-index"}
        )

        assert response.status_code == 500
        data = await response.get_json()
        assert "error" in data


@pytest.mark.asyncio
async def test_upload_images_validation_error(client):
    """Test upload images endpoint validation for missing data field.

    The endpoint returns 200 with per-image results (not 400) for bulk operations,
    allowing partial success. Images missing required fields are marked as failed.
    """
    # Missing required data field
    response = await client.post(
        "/api/admin/upload-images",
        json={
            "images": [
                {"filename": "test.jpg", "content_type": "image/jpeg"}
                # Missing "data" field
            ]
        }
    )

    # Endpoint returns 200 with per-image results for bulk operations
    assert response.status_code == 200
    data = await response.get_json()

    # Should indicate failure at the operation level
    assert data["success"] is False
    assert data["failed"] == 1
    assert data["uploaded"] == 0

    # Should have detailed per-image failure info
    assert len(data["results"]) == 1
    assert data["results"][0]["status"] == "failed"
    assert "Missing filename or data" in data["results"][0]["error"]
