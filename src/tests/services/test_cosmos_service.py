from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from services.cosmos_service import CosmosDBService


@pytest.fixture
def mock_cosmos_service():
    """Create a mocked CosmosDB service for reuse across test sections."""
    with patch("services.cosmos_service.app_settings") as mock_settings, \
         patch("services.cosmos_service.DefaultAzureCredential"), \
         patch("services.cosmos_service.CosmosClient") as mock_client:

        mock_settings.base_settings.azure_client_id = None
        mock_settings.cosmos.endpoint = "https://test.documents.azure.com"
        mock_settings.cosmos.database_name = "testdb"
        mock_settings.cosmos.products_container = "products"
        mock_settings.cosmos.conversations_container = "conversations"

        mock_cosmos_client = MagicMock()
        mock_database = MagicMock()
        mock_products_container = MagicMock()
        mock_conversations_container = MagicMock()

        mock_cosmos_client.get_database_client.return_value = mock_database
        mock_database.get_container_client.side_effect = lambda name: (
            mock_products_container if name == "products" else mock_conversations_container
        )
        mock_client.return_value = mock_cosmos_client

        service = CosmosDBService()
        service._mock_products_container = mock_products_container
        service._mock_conversations_container = mock_conversations_container

        yield service


@pytest.mark.asyncio
async def test_initialize_with_managed_identity():
    """Test initialization with managed identity credential."""
    with patch("services.cosmos_service.app_settings") as mock_settings, \
         patch("services.cosmos_service.ManagedIdentityCredential") as mock_cred, \
         patch("services.cosmos_service.CosmosClient") as mock_client:

        # Configure settings
        mock_settings.base_settings.azure_client_id = "test-client-id"
        mock_settings.cosmos.endpoint = "https://test.documents.azure.com"
        mock_settings.cosmos.database_name = "testdb"
        mock_settings.cosmos.products_container = "products"
        mock_settings.cosmos.conversations_container = "conversations"

        mock_credential = AsyncMock()
        mock_cred.return_value = mock_credential

        mock_cosmos_client = MagicMock()
        mock_database = MagicMock()
        mock_cosmos_client.get_database_client.return_value = mock_database
        mock_database.get_container_client.return_value = MagicMock()
        mock_client.return_value = mock_cosmos_client

        service = CosmosDBService()
        await service.initialize()

        # Verify managed identity was used
        mock_cred.assert_called_once_with(client_id="test-client-id")
        mock_client.assert_called_once()


@pytest.mark.asyncio
async def test_initialize_with_default_credential():
    """Test initialization with default Azure credential."""
    with patch("services.cosmos_service.app_settings") as mock_settings, \
         patch("services.cosmos_service.DefaultAzureCredential") as mock_cred, \
         patch("services.cosmos_service.CosmosClient") as mock_client:

        # No client ID = use default credential
        mock_settings.base_settings.azure_client_id = None
        mock_settings.cosmos.endpoint = "https://test.documents.azure.com"
        mock_settings.cosmos.database_name = "testdb"
        mock_settings.cosmos.products_container = "products"
        mock_settings.cosmos.conversations_container = "conversations"

        mock_credential = AsyncMock()
        mock_cred.return_value = mock_credential

        mock_cosmos_client = MagicMock()
        mock_database = MagicMock()
        mock_cosmos_client.get_database_client.return_value = mock_database
        mock_database.get_container_client.return_value = MagicMock()
        mock_client.return_value = mock_cosmos_client

        service = CosmosDBService()
        await service.initialize()

        mock_cred.assert_called_once()


@pytest.mark.asyncio
async def test_close_client():
    """Test closing the CosmosDB client."""
    with patch("services.cosmos_service.app_settings") as mock_settings, \
         patch("services.cosmos_service.DefaultAzureCredential"), \
         patch("services.cosmos_service.CosmosClient") as mock_client:

        mock_settings.base_settings.azure_client_id = None
        mock_settings.cosmos.endpoint = "https://test.documents.azure.com"
        mock_settings.cosmos.database_name = "testdb"
        mock_settings.cosmos.products_container = "products"
        mock_settings.cosmos.conversations_container = "conversations"

        mock_cosmos_client = MagicMock()
        mock_cosmos_client.close = AsyncMock()
        mock_database = MagicMock()
        mock_cosmos_client.get_database_client.return_value = mock_database
        mock_database.get_container_client.return_value = MagicMock()
        mock_client.return_value = mock_cosmos_client

        service = CosmosDBService()
        await service.initialize()
        await service.close()

        mock_cosmos_client.close.assert_called_once()
        assert service._client is None


@pytest.mark.asyncio
async def test_get_product_by_sku_found(mock_cosmos_service):
    """Test retrieving a product by SKU when it exists."""
    sample_product_data = {
        "sku": "TEST-SKU-123",
        "product_id": "prod-123",
        "product_name": "Test Product",
        "category": "Interior",
        "sub_category": "Paint",
        "marketing_description": "Great paint",
        "detailed_spec_description": "Detailed specs",
        "model": "Model X",
        "description": "Product description",
        "tags": "paint, interior",
        "price": 29.99
    }

    async def mock_query(*_args, **_kwargs):
        yield sample_product_data

    mock_cosmos_service._mock_products_container.query_items = mock_query

    await mock_cosmos_service.initialize()
    product = await mock_cosmos_service.get_product_by_sku("TEST-SKU-123")

    assert product is not None
    assert product.sku == "TEST-SKU-123"
    assert product.product_name == "Test Product"


@pytest.mark.asyncio
async def test_get_product_by_sku_not_found(mock_cosmos_service):
    """Test retrieving a product by SKU when it doesn't exist."""
    async def mock_query(*_args, **_kwargs):
        if False:
            yield  # Empty async generator

    mock_cosmos_service._mock_products_container.query_items = mock_query

    await mock_cosmos_service.initialize()
    product = await mock_cosmos_service.get_product_by_sku("NONEXISTENT")

    assert product is None


@pytest.mark.asyncio
async def test_get_products_by_category(mock_cosmos_service):
    """Test retrieving products by category."""
    sample_products = [
        {
            "sku": "PAINT-001",
            "product_id": "prod-1",
            "product_name": "Interior Paint",
            "category": "Interior",
            "sub_category": "Paint",
            "marketing_description": "Great paint",
            "detailed_spec_description": "Specs",
            "model": "Model X",
            "description": "Description",
            "tags": "paint",
            "price": 29.99
        }
    ]

    async def mock_query(*_args, **_kwargs):
        for p in sample_products:
            yield p

    mock_cosmos_service._mock_products_container.query_items = mock_query

    await mock_cosmos_service.initialize()
    products = await mock_cosmos_service.get_products_by_category("Interior")

    assert len(products) == 1
    assert products[0].category == "Interior"


@pytest.mark.asyncio
async def test_get_products_by_category_with_subcategory(mock_cosmos_service):
    """Test retrieving products by category and sub-category."""
    sample_products = [
        {
            "sku": "PAINT-001",
            "product_id": "prod-1",
            "product_name": "Interior Paint",
            "category": "Interior",
            "sub_category": "Paint",
            "marketing_description": "Great paint",
            "detailed_spec_description": "Specs",
            "model": "Model X",
            "description": "Description",
            "tags": "paint",
            "price": 29.99
        }
    ]

    async def mock_query(*_args, **_kwargs):
        for p in sample_products:
            yield p

    mock_cosmos_service._mock_products_container.query_items = mock_query

    await mock_cosmos_service.initialize()
    products = await mock_cosmos_service.get_products_by_category("Interior", "Paint")

    assert len(products) == 1
    assert products[0].sub_category == "Paint"


@pytest.mark.asyncio
async def test_search_products(mock_cosmos_service):
    """Test searching products by term."""
    sample_products = [
        {
            "sku": "PAINT-001",
            "product_id": "prod-1",
            "product_name": "Interior Paint Premium",
            "category": "Interior",
            "sub_category": "Paint",
            "marketing_description": "Premium quality paint",
            "detailed_spec_description": "Specs",
            "model": "Model X",
            "description": "Description",
            "tags": "paint, premium",
            "price": 29.99
        }
    ]

    async def mock_query(*_args, **_kwargs):
        for p in sample_products:
            yield p

    mock_cosmos_service._mock_products_container.query_items = mock_query

    await mock_cosmos_service.initialize()
    products = await mock_cosmos_service.search_products("Premium")

    assert len(products) == 1
    assert "Premium" in products[0].product_name


@pytest.mark.asyncio
async def test_upsert_product(mock_cosmos_service):
    """Test creating/updating a product."""
    product_data = {
        "sku": "NEW-SKU-123",
        "product_id": "prod-new",
        "product_name": "New Product",
        "category": "Interior",
        "sub_category": "Paint",
        "marketing_description": "New product desc",
        "detailed_spec_description": "Specs",
        "model": "Model Y",
        "description": "Description",
        "tags": "new, paint",
        "price": 39.99
    }

    mock_cosmos_service._mock_products_container.upsert_item = AsyncMock(
        return_value={**product_data, "id": "NEW-SKU-123", "updated_at": "2024-01-01T00:00:00Z"}
    )

    await mock_cosmos_service.initialize()

    from models import Product  # noqa: F811
    product = Product(**product_data)
    result = await mock_cosmos_service.upsert_product(product)

    assert result.sku == "NEW-SKU-123"
    mock_cosmos_service._mock_products_container.upsert_item.assert_called_once()


@pytest.mark.asyncio
async def test_delete_product_success(mock_cosmos_service):
    """Test deleting a product successfully."""
    mock_cosmos_service._mock_products_container.delete_item = AsyncMock()

    await mock_cosmos_service.initialize()
    result = await mock_cosmos_service.delete_product("TEST-SKU")

    assert result is True
    mock_cosmos_service._mock_products_container.delete_item.assert_called_once()


@pytest.mark.asyncio
async def test_delete_product_failure(mock_cosmos_service):
    """Test deleting a product that fails."""
    mock_cosmos_service._mock_products_container.delete_item = AsyncMock(
        side_effect=Exception("Delete failed")
    )

    await mock_cosmos_service.initialize()
    result = await mock_cosmos_service.delete_product("NONEXISTENT")

    assert result is False


@pytest.mark.asyncio
async def test_delete_all_products(mock_cosmos_service):
    """Test deleting all products."""
    items = [{"id": "SKU-1"}, {"id": "SKU-2"}]

    async def mock_query(*_args, **_kwargs):
        for item in items:
            yield item

    mock_cosmos_service._mock_products_container.query_items = mock_query
    mock_cosmos_service._mock_products_container.delete_item = AsyncMock()

    await mock_cosmos_service.initialize()
    count = await mock_cosmos_service.delete_all_products()

    assert count == 2
    assert mock_cosmos_service._mock_products_container.delete_item.call_count == 2


@pytest.mark.asyncio
async def test_delete_all_products_with_failures(mock_cosmos_service):
    """Test delete_all_products handles individual delete failures gracefully."""
    items = [{"id": "SKU-1"}, {"id": "SKU-2"}, {"id": "SKU-3"}]

    async def mock_query(*_args, **_kwargs):
        for item in items:
            yield item

    delete_count = 0

    async def mock_delete(*_args, **_kwargs):
        nonlocal delete_count
        delete_count += 1
        if delete_count == 2:
            raise Exception("Delete failed for item 2")

    mock_cosmos_service._mock_products_container.query_items = mock_query
    mock_cosmos_service._mock_products_container.delete_item = mock_delete

    await mock_cosmos_service.initialize()
    count = await mock_cosmos_service.delete_all_products()

    # Should return 2 deleted (first and third succeeded, second failed)
    assert count == 2


@pytest.mark.asyncio
async def test_get_all_products(mock_cosmos_service):
    """Test retrieving all products."""
    sample_products = [
        {
            "sku": f"SKU-{i}",
            "product_id": f"prod-{i}",
            "product_name": f"Product {i}",
            "category": "Interior",
            "sub_category": "Paint",
            "marketing_description": "Description",
            "detailed_spec_description": "Specs",
            "model": "Model",
            "description": "Desc",
            "tags": "paint",
            "price": 19.99
        }
        for i in range(3)
    ]

    async def mock_query(*_args, **_kwargs):
        for p in sample_products:
            yield p

    mock_cosmos_service._mock_products_container.query_items = mock_query

    await mock_cosmos_service.initialize()
    products = await mock_cosmos_service.get_all_products(limit=10)

    assert len(products) == 3


@pytest.mark.asyncio
async def test_get_conversation_found(mock_cosmos_service):
    """Test getting a conversation that exists."""
    conversation_data = {
        "id": "conv-123",
        "user_id": "user-123",
        "title": "Test Conversation",
        "messages": []
    }

    mock_cosmos_service._mock_conversations_container.read_item = AsyncMock(
        return_value=conversation_data
    )

    await mock_cosmos_service.initialize()
    result = await mock_cosmos_service.get_conversation("conv-123", "user-123")

    assert result is not None
    assert result["id"] == "conv-123"


@pytest.mark.asyncio
async def test_get_conversation_not_found(mock_cosmos_service):
    """Test getting a conversation that doesn't exist."""
    mock_cosmos_service._mock_conversations_container.read_item = AsyncMock(
        side_effect=Exception("Not found")
    )

    async def mock_query(*_args, **_kwargs):
        if False:
            yield  # Empty

    mock_cosmos_service._mock_conversations_container.query_items = mock_query

    await mock_cosmos_service.initialize()
    result = await mock_cosmos_service.get_conversation("nonexistent", "user-123")

    assert result is None


@pytest.mark.asyncio
async def test_get_user_conversations(mock_cosmos_service):
    """Test getting all conversations for a user."""
    conversations = [
        {"id": "conv-1", "user_id": "user-123", "title": "Conv 1"},
        {"id": "conv-2", "user_id": "user-123", "title": "Conv 2"}
    ]

    async def mock_query(*_args, **_kwargs):
        for c in conversations:
            yield c

    mock_cosmos_service._mock_conversations_container.query_items = mock_query

    await mock_cosmos_service.initialize()
    result = await mock_cosmos_service.get_user_conversations("user-123", limit=10)

    assert len(result) == 2


@pytest.mark.asyncio
async def test_delete_conversation(mock_cosmos_service):
    """Test deleting a conversation."""
    # get_conversation returns the conversation to get partition key
    with patch.object(mock_cosmos_service, 'get_conversation', new=AsyncMock(return_value={
        "id": "conv-123",
        "userId": "user-123",
        "title": "Test"
    })):
        mock_cosmos_service._mock_conversations_container.delete_item = AsyncMock()

        await mock_cosmos_service.initialize()
        result = await mock_cosmos_service.delete_conversation("conv-123", "user-123")

        assert result is True
        mock_cosmos_service._mock_conversations_container.delete_item.assert_called_once()


@pytest.mark.asyncio
async def test_rename_conversation_success(mock_cosmos_service):
    """Test renaming a conversation successfully."""
    existing_conv = {
        "id": "conv-123",
        "user_id": "user-123",
        "title": "Old Title",
        "messages": []
    }
    updated_conv = {
        "id": "conv-123",
        "user_id": "user-123",
        "userId": "user-123",
        "title": "Old Title",
        "messages": [],
        "metadata": {"custom_title": "New Title"}
    }

    with patch.object(mock_cosmos_service, 'get_conversation', new=AsyncMock(return_value=existing_conv)):
        mock_cosmos_service._mock_conversations_container.upsert_item = AsyncMock(
            return_value=updated_conv
        )

        await mock_cosmos_service.initialize()
        result = await mock_cosmos_service.rename_conversation("conv-123", "user-123", "New Title")

        assert result is not None
        assert result.get("metadata", {}).get("custom_title") == "New Title"


@pytest.mark.asyncio
async def test_rename_conversation_not_found(mock_cosmos_service):
    """Test renaming a conversation that doesn't exist."""
    with patch.object(mock_cosmos_service, 'get_conversation', new=AsyncMock(return_value=None)):
        await mock_cosmos_service.initialize()
        result = await mock_cosmos_service.rename_conversation("nonexistent", "user-123", "New Title")

        assert result is None


@pytest.mark.asyncio
async def test_add_message_to_conversation_new(mock_cosmos_service):
    """Test adding a message to a new conversation."""
    mock_cosmos_service._mock_conversations_container.read_item = AsyncMock(
        side_effect=Exception("Not found")
    )
    mock_cosmos_service._mock_conversations_container.upsert_item = AsyncMock(
        return_value={"id": "conv-123", "messages": []}
    )

    await mock_cosmos_service.initialize()

    message = {
        "role": "user",
        "content": "Hello",
        "timestamp": "2024-01-01T00:00:00Z"
    }
    await mock_cosmos_service.add_message_to_conversation("conv-123", "user-123", message)

    mock_cosmos_service._mock_conversations_container.upsert_item.assert_called_once()


@pytest.mark.asyncio
async def test_add_message_to_existing_conversation(mock_cosmos_service):
    """Test adding a message to an existing conversation."""
    existing_conv = {
        "id": "conv-123",
        "user_id": "user-123",
        "messages": [{"role": "user", "content": "Previous message"}]
    }

    mock_cosmos_service._mock_conversations_container.read_item = AsyncMock(
        return_value=existing_conv
    )
    mock_cosmos_service._mock_conversations_container.upsert_item = AsyncMock(
        return_value=existing_conv
    )

    await mock_cosmos_service.initialize()

    message = {
        "role": "assistant",
        "content": "Response",
        "timestamp": "2024-01-01T00:00:00Z"
    }
    await mock_cosmos_service.add_message_to_conversation("conv-123", "user-123", message)

    # Check that message was appended
    call_args = mock_cosmos_service._mock_conversations_container.upsert_item.call_args
    upserted_doc = call_args[0][0]
    assert len(upserted_doc["messages"]) == 2


@pytest.mark.asyncio
async def test_save_generated_content_existing_conversation(mock_cosmos_service):
    """Test saving generated content to an existing conversation."""
    existing_conv = {
        "id": "conv-123",
        "user_id": "user-123",
        "userId": "user-123",
        "messages": [],
        "generated_content": None
    }

    with patch.object(mock_cosmos_service, 'get_conversation', new=AsyncMock(return_value=existing_conv)):
        mock_cosmos_service._mock_conversations_container.upsert_item = AsyncMock(
            return_value={**existing_conv, "generated_content": {"headline": "Test"}}
        )

        await mock_cosmos_service.initialize()
        result = await mock_cosmos_service.save_generated_content(
            "conv-123",
            "user-123",
            {"headline": "Test", "body": "Test body"}
        )

        assert result is not None
        mock_cosmos_service._mock_conversations_container.upsert_item.assert_called_once()


@pytest.mark.asyncio
async def test_save_generated_content_new_conversation(mock_cosmos_service):
    """Test saving generated content creates new conversation if not exists."""
    with patch.object(mock_cosmos_service, 'get_conversation', new=AsyncMock(return_value=None)):
        mock_cosmos_service._mock_conversations_container.upsert_item = AsyncMock(
            return_value={"id": "conv-new", "generated_content": {"headline": "Test"}}
        )

        await mock_cosmos_service.initialize()
        result = await mock_cosmos_service.save_generated_content(
            "conv-new",
            "user-123",
            {"headline": "Test"}
        )

        assert result is not None
        mock_cosmos_service._mock_conversations_container.upsert_item.assert_called_once()


@pytest.mark.asyncio
async def test_save_generated_content_migrates_userid(mock_cosmos_service):
    """Test that save_generated_content migrates old documents without userId."""
    # Old document without userId field
    existing_conv = {
        "id": "conv-legacy",
        "user_id": "user-123",
        "messages": [],
        "generated_content": None
    }

    with patch.object(mock_cosmos_service, 'get_conversation', new=AsyncMock(return_value=existing_conv)):
        mock_cosmos_service._mock_conversations_container.upsert_item = AsyncMock(
            return_value=existing_conv
        )

        await mock_cosmos_service.initialize()
        await mock_cosmos_service.save_generated_content(
            "conv-legacy",
            "user-123",
            {"headline": "Test"}
        )

        # Check that userId was added for partition key
        call_args = mock_cosmos_service._mock_conversations_container.upsert_item.call_args
        upserted_doc = call_args[0][0]
        assert upserted_doc.get("userId") == "user-123"


@pytest.mark.asyncio
async def test_get_user_conversations_anonymous(mock_cosmos_service):
    """Test getting conversations for anonymous user includes legacy data."""
    conversations = [
        {
            "id": "conv-1",
            "userId": "anonymous",
            "user_id": "anonymous",
            "messages": [{"role": "user", "content": "First message"}],
            "brief": {"overview": "Test campaign"}
        }
    ]

    async def mock_query(*_args, **_kwargs):
        for c in conversations:
            yield c

    mock_cosmos_service._mock_conversations_container.query_items = mock_query

    await mock_cosmos_service.initialize()
    result = await mock_cosmos_service.get_user_conversations("anonymous", limit=10)

    assert len(result) == 1
    # Title should come from brief overview
    assert "Test campaign" in result[0]["title"]


@pytest.mark.asyncio
async def test_get_user_conversations_with_custom_title(mock_cosmos_service):
    """Test conversation title from custom metadata."""
    conversations = [
        {
            "id": "conv-1",
            "userId": "user-123",
            "user_id": "user-123",
            "messages": [],
            "metadata": {"custom_title": "My Custom Title"}
        }
    ]

    async def mock_query(*_args, **_kwargs):
        for c in conversations:
            yield c

    mock_cosmos_service._mock_conversations_container.query_items = mock_query

    await mock_cosmos_service.initialize()
    result = await mock_cosmos_service.get_user_conversations("user-123", limit=10)

    assert result[0]["title"] == "My Custom Title"


@pytest.mark.asyncio
async def test_get_user_conversations_no_title_fallback(mock_cosmos_service):
    """Test conversation title falls back to New Conversation when no info available."""
    conversations = [
        {
            "id": "conv-1",
            "userId": "user-123",
            "user_id": "user-123",
            "messages": [],  # No messages
            "brief": None,  # No brief
            "metadata": None  # No metadata
        }
    ]

    async def mock_query(*_args, **_kwargs):
        for c in conversations:
            yield c

    mock_cosmos_service._mock_conversations_container.query_items = mock_query

    await mock_cosmos_service.initialize()
    result = await mock_cosmos_service.get_user_conversations("user-123", limit=10)

    assert result[0]["title"] == "New Conversation"


@pytest.mark.asyncio
async def test_get_user_conversations_title_from_first_user_message(mock_cosmos_service):
    """Test conversation title extracted from first user message when no custom title or brief."""
    conversations = [
        {
            "id": "conv-1",
            "userId": "user-123",
            "user_id": "user-123",
            "messages": [
                {"role": "user", "content": "Create a marketing campaign for summer"},
                {"role": "assistant", "content": "I'd be happy to help..."}
            ],
            "brief": {},  # Empty brief (no overview)
            "metadata": {}  # Empty metadata (no custom_title)
        }
    ]

    async def mock_query(*_args, **_kwargs):
        for c in conversations:
            yield c

    mock_cosmos_service._mock_conversations_container.query_items = mock_query

    await mock_cosmos_service.initialize()
    result = await mock_cosmos_service.get_user_conversations("user-123", limit=10)

    # Title should be from first user message, truncated to 4 words
    assert result[0]["title"] == "Create a marketing campaign"


@pytest.mark.asyncio
async def test_get_user_conversations_title_from_user_message_skips_assistant(mock_cosmos_service):
    """Test that title extraction finds first USER message, skipping assistant messages."""
    conversations = [
        {
            "id": "conv-1",
            "userId": "user-123",
            "user_id": "user-123",
            "messages": [
                {"role": "assistant", "content": "Welcome! How can I help?"},
                {"role": "user", "content": "Help with product launch"},
                {"role": "assistant", "content": "Sure thing!"}
            ],
            "brief": None,
            "metadata": None
        }
    ]

    async def mock_query(*_args, **_kwargs):
        for c in conversations:
            yield c

    mock_cosmos_service._mock_conversations_container.query_items = mock_query

    await mock_cosmos_service.initialize()
    result = await mock_cosmos_service.get_user_conversations("user-123", limit=10)

    # Should get the USER message, not assistant
    assert result[0]["title"] == "Help with product launch"


@pytest.mark.asyncio
async def test_get_conversation_cross_partition_exception_logs_warning(mock_cosmos_service):
    """Test that cross-partition query failure logs a warning and returns None."""
    # First read_item fails (not found)
    mock_cosmos_service._mock_conversations_container.read_item = AsyncMock(
        side_effect=Exception("Not found")
    )

    # Cross-partition query also fails
    async def mock_query_fails(*_args, **_kwargs):
        if False:
            yield  # Makes this an async generator
        raise Exception("Cross-partition query failed")

    mock_cosmos_service._mock_conversations_container.query_items = mock_query_fails

    await mock_cosmos_service.initialize()

    with patch("services.cosmos_service.logger") as mock_logger:
        result = await mock_cosmos_service.get_conversation("conv-123", "user-123")

        assert result is None
        # Verify warning was logged
        mock_logger.warning.assert_called()
        call_args = mock_logger.warning.call_args[0]
        assert "Cross-partition" in call_args[0]


@pytest.mark.asyncio
async def test_delete_conversation_raises_exception_on_failure(mock_cosmos_service):
    """Test that delete_conversation raises exception when delete fails."""
    existing_conv = {
        "id": "conv-123",
        "userId": "user-123",
        "user_id": "user-123",
        "messages": []
    }

    # Mock get_conversation to return existing conversation
    with patch.object(mock_cosmos_service, 'get_conversation', new=AsyncMock(return_value=existing_conv)):
        # Mock delete_item to fail
        mock_cosmos_service._mock_conversations_container.delete_item = AsyncMock(
            side_effect=Exception("Permission denied")
        )

        await mock_cosmos_service.initialize()

        with pytest.raises(Exception) as exc_info:
            await mock_cosmos_service.delete_conversation("conv-123", "user-123")

        assert "Permission denied" in str(exc_info.value)


@pytest.mark.asyncio
async def test_get_cosmos_service_creates_singleton():
    """Test that get_cosmos_service creates and returns singleton instance."""
    import services.cosmos_service as cosmos_module

    # Reset singleton
    cosmos_module._cosmos_service = None

    with patch("services.cosmos_service.app_settings") as mock_settings, \
         patch("services.cosmos_service.DefaultAzureCredential"), \
         patch("services.cosmos_service.CosmosClient") as mock_client:

        mock_settings.base_settings.azure_client_id = None
        mock_settings.cosmos.endpoint = "https://test.documents.azure.com"
        mock_settings.cosmos.database_name = "testdb"
        mock_settings.cosmos.products_container = "products"
        mock_settings.cosmos.conversations_container = "conversations"

        mock_cosmos_client = MagicMock()
        mock_database = MagicMock()
        mock_cosmos_client.get_database_client.return_value = mock_database
        mock_database.get_container_client.return_value = MagicMock()
        mock_client.return_value = mock_cosmos_client

        # First call creates instance
        service1 = await cosmos_module.get_cosmos_service()
        assert service1 is not None
        assert cosmos_module._cosmos_service is service1

        # Second call returns same instance
        service2 = await cosmos_module.get_cosmos_service()
        assert service2 is service1

    # Reset singleton after test
    cosmos_module._cosmos_service = None


@pytest.mark.asyncio
async def test_get_cosmos_service_initializes_on_first_call():
    """Test that get_cosmos_service initializes the service on first call."""
    import services.cosmos_service as cosmos_module

    # Reset singleton
    cosmos_module._cosmos_service = None

    with patch("services.cosmos_service.app_settings") as mock_settings, \
         patch("services.cosmos_service.DefaultAzureCredential"), \
         patch("services.cosmos_service.CosmosClient") as mock_client:

        mock_settings.base_settings.azure_client_id = None
        mock_settings.cosmos.endpoint = "https://test.documents.azure.com"
        mock_settings.cosmos.database_name = "testdb"
        mock_settings.cosmos.products_container = "products"
        mock_settings.cosmos.conversations_container = "conversations"

        mock_cosmos_client = MagicMock()
        mock_database = MagicMock()
        mock_cosmos_client.get_database_client.return_value = mock_database
        mock_database.get_container_client.return_value = MagicMock()
        mock_client.return_value = mock_cosmos_client

        _ = await cosmos_module.get_cosmos_service()

        # Verify CosmosClient was created (initialization happened)
        mock_client.assert_called()

    # Reset singleton after test
    cosmos_module._cosmos_service = None
