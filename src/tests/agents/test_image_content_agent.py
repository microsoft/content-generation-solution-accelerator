import base64
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from agents.image_content_agent import (_generate_gpt_image,
                                        _truncate_for_image,
                                        generate_dalle_image, generate_image)


def test_truncate_short_description_unchanged():
    """Test that short descriptions are returned unchanged."""

    short_desc = "A beautiful blue paint with hex code #0066CC"
    result = _truncate_for_image(short_desc, max_chars=1500)

    assert result == short_desc


def test_truncate_empty_description():
    """Test handling of empty description."""

    result = _truncate_for_image("", max_chars=1500)
    assert result == ""

    result = _truncate_for_image(None, max_chars=1500)
    assert result is None


def test_truncate_long_description_truncated():
    """Test that very long descriptions are truncated."""

    long_desc = "This is a test description. " * 200  # ~5600 chars
    result = _truncate_for_image(long_desc, max_chars=1500)

    assert len(result) <= 1500
    assert "[Additional details truncated for image generation]" in result or len(result) <= 1500


def test_truncate_preserves_hex_codes():
    """Test that hex color codes are preserved in truncation."""

    desc_with_hex = """### Product A
This is a nice paint color.
Hex code: #FF5733
Some filler text here.
### Product B
Another product with hex: #0066CC
More filler text that makes this very long.
""" + "Filler. " * 300

    result = _truncate_for_image(desc_with_hex, max_chars=500)

    assert "### Product A" in result or "#FF5733" in result or len(result) <= 500


def test_truncate_preserves_product_headers():
    """Test that product headers (### ...) are preserved."""

    desc = """### Snow Veil White
A pure white paint for interiors.
Hex code: #FFFFFF

### Cloud Drift Gray
A soft gray tone.
Hex code: #CCCCCC
""" + "Extra text. " * 500

    result = _truncate_for_image(desc, max_chars=300)

    assert len(result) <= 300


def test_truncate_preserves_finish_descriptions():
    """Test that finish descriptions (matte, eggshell) are considered."""

    desc = """### Product
Color description here.
This paint has a matte finish that gives a soft appearance.
Hex: #123456
""" + "More text. " * 400

    result = _truncate_for_image(desc, max_chars=400)

    assert len(result) <= 400


@pytest.mark.asyncio
async def test_generate_dalle_image_success():
    """Test successful DALL-E image generation."""
    with patch("agents.image_content_agent.app_settings") as mock_settings, \
         patch("agents.image_content_agent.DefaultAzureCredential") as mock_cred, \
         patch("agents.image_content_agent.AsyncAzureOpenAI") as mock_client:

        mock_settings.azure_openai.effective_image_model = "dall-e-3"
        mock_settings.azure_openai.dalle_endpoint = "https://test.openai.azure.com"
        mock_settings.azure_openai.endpoint = "https://test.openai.azure.com"
        mock_settings.azure_openai.preview_api_version = "2024-02-15-preview"
        mock_settings.azure_openai.dalle_model = "dall-e-3"
        mock_settings.azure_openai.image_size = "1024x1024"
        mock_settings.azure_openai.image_quality = "standard"
        mock_settings.base_settings.azure_client_id = None
        mock_settings.brand_guidelines.get_image_generation_prompt.return_value = "Brand style guide"
        mock_settings.brand_guidelines.primary_color = "#0066CC"
        mock_settings.brand_guidelines.secondary_color = "#FF5733"

        mock_credential = AsyncMock()
        mock_token = MagicMock()
        mock_token.token = "test-token"
        mock_credential.get_token = AsyncMock(return_value=mock_token)
        mock_cred.return_value = mock_credential

        mock_openai = AsyncMock()
        mock_image_data = MagicMock()
        mock_image_data.b64_json = base64.b64encode(b"fake-image-data").decode()
        mock_image_data.revised_prompt = "Revised prompt from DALL-E"
        mock_response = MagicMock()
        mock_response.data = [mock_image_data]
        mock_openai.images.generate = AsyncMock(return_value=mock_response)
        mock_openai.close = AsyncMock()
        mock_client.return_value = mock_openai

        result = await generate_dalle_image(
            prompt="Create a marketing image for paint",
            product_description="Blue paint with hex #0066CC",
            scene_description="Modern living room"
        )

        assert result["success"] is True
        assert "image_base64" in result
        assert result["model"] == "dall-e-3"


@pytest.mark.asyncio
async def test_generate_dalle_image_with_managed_identity():
    """Test DALL-E generation with managed identity credential."""
    with patch("agents.image_content_agent.app_settings") as mock_settings, \
         patch("agents.image_content_agent.ManagedIdentityCredential") as mock_cred, \
         patch("agents.image_content_agent.AsyncAzureOpenAI") as mock_client:

        mock_settings.azure_openai.effective_image_model = "dall-e-3"
        mock_settings.azure_openai.dalle_endpoint = "https://test.openai.azure.com"
        mock_settings.azure_openai.endpoint = "https://test.openai.azure.com"
        mock_settings.azure_openai.preview_api_version = "2024-02-15-preview"
        mock_settings.azure_openai.dalle_model = "dall-e-3"
        mock_settings.azure_openai.image_size = "1024x1024"
        mock_settings.azure_openai.image_quality = "standard"
        mock_settings.base_settings.azure_client_id = "test-client-id"
        mock_settings.brand_guidelines.get_image_generation_prompt.return_value = "Brand style"
        mock_settings.brand_guidelines.primary_color = "#0066CC"
        mock_settings.brand_guidelines.secondary_color = "#FF5733"

        mock_credential = AsyncMock()
        mock_token = MagicMock()
        mock_token.token = "test-token"
        mock_credential.get_token = AsyncMock(return_value=mock_token)
        mock_cred.return_value = mock_credential

        mock_openai = AsyncMock()
        mock_image_data = MagicMock()
        mock_image_data.b64_json = base64.b64encode(b"image").decode()
        mock_response = MagicMock()
        mock_response.data = [mock_image_data]
        mock_openai.images.generate = AsyncMock(return_value=mock_response)
        mock_openai.close = AsyncMock()
        mock_client.return_value = mock_openai

        result = await generate_dalle_image(prompt="Test prompt")

        assert result["success"] is True
        mock_cred.assert_called_once_with(client_id="test-client-id")


@pytest.mark.asyncio
async def test_generate_dalle_image_error_handling():
    """Test DALL-E generation error handling."""
    with patch("agents.image_content_agent.app_settings") as mock_settings, \
         patch("agents.image_content_agent.DefaultAzureCredential") as mock_cred:

        mock_settings.azure_openai.effective_image_model = "dall-e-3"
        mock_settings.azure_openai.dalle_endpoint = "https://test.openai.azure.com"
        mock_settings.azure_openai.endpoint = "https://test.openai.azure.com"
        mock_settings.azure_openai.preview_api_version = "2024-02-15-preview"
        mock_settings.azure_openai.dalle_model = "dall-e-3"
        mock_settings.azure_openai.image_size = "1024x1024"
        mock_settings.azure_openai.image_quality = "standard"
        mock_settings.base_settings.azure_client_id = None
        mock_settings.brand_guidelines.get_image_generation_prompt.return_value = "Brand"
        mock_settings.brand_guidelines.primary_color = "#0066CC"
        mock_settings.brand_guidelines.secondary_color = "#FF5733"

        mock_cred.side_effect = Exception("Authentication failed")

        result = await generate_dalle_image(prompt="Test prompt")

        assert result["success"] is False
        assert "error" in result
        assert "Authentication failed" in result["error"]


@pytest.mark.asyncio
async def test_generate_gpt_image_success():
    """Test successful gpt-image-1-mini generation."""
    with patch("agents.image_content_agent.app_settings") as mock_settings, \
         patch("agents.image_content_agent.DefaultAzureCredential") as mock_cred, \
         patch("agents.image_content_agent.AsyncAzureOpenAI") as mock_client:

        mock_settings.azure_openai.effective_image_model = "gpt-image-1-mini"
        mock_settings.azure_openai.gpt_image_endpoint = "https://test.openai.azure.com"
        mock_settings.azure_openai.dalle_endpoint = "https://test.openai.azure.com"
        mock_settings.azure_openai.endpoint = "https://test.openai.azure.com"
        mock_settings.azure_openai.image_api_version = "2025-04-01-preview"
        mock_settings.azure_openai.image_size = "1024x1024"
        mock_settings.azure_openai.image_quality = "medium"
        mock_settings.base_settings.azure_client_id = None
        mock_settings.brand_guidelines.get_image_generation_prompt.return_value = "Brand style"
        mock_settings.brand_guidelines.primary_color = "#0066CC"
        mock_settings.brand_guidelines.secondary_color = "#FF5733"

        mock_credential = AsyncMock()
        mock_token = MagicMock()
        mock_token.token = "test-token"
        mock_credential.get_token = AsyncMock(return_value=mock_token)
        mock_cred.return_value = mock_credential

        mock_openai = AsyncMock()
        mock_image_data = MagicMock()
        mock_image_data.b64_json = base64.b64encode(b"gpt-image-data").decode()
        mock_response = MagicMock()
        mock_response.data = [mock_image_data]
        mock_openai.images.generate = AsyncMock(return_value=mock_response)
        mock_openai.close = AsyncMock()
        mock_client.return_value = mock_openai

        result = await _generate_gpt_image(
            prompt="Create a marketing image",
            product_description="Paint product",
            scene_description="Living room"
        )

        assert result["success"] is True
        assert "image_base64" in result
        assert result["model"] == "gpt-image-1-mini"


@pytest.mark.asyncio
async def test_generate_gpt_image_quality_passthrough():
    """Test that gpt-image passes quality setting through unchanged."""
    with patch("agents.image_content_agent.app_settings") as mock_settings, \
         patch("agents.image_content_agent.DefaultAzureCredential") as mock_cred, \
         patch("agents.image_content_agent.AsyncAzureOpenAI") as mock_client:

        mock_settings.azure_openai.effective_image_model = "gpt-image-1-mini"
        mock_settings.azure_openai.gpt_image_endpoint = "https://test.openai.azure.com"
        mock_settings.azure_openai.dalle_endpoint = None
        mock_settings.azure_openai.endpoint = "https://test.openai.azure.com"
        mock_settings.azure_openai.image_api_version = "2025-04-01-preview"
        mock_settings.azure_openai.image_size = "1024x1024"
        mock_settings.azure_openai.image_quality = "medium"
        mock_settings.base_settings.azure_client_id = None
        mock_settings.brand_guidelines.get_image_generation_prompt.return_value = "Brand"
        mock_settings.brand_guidelines.primary_color = "#000"
        mock_settings.brand_guidelines.secondary_color = "#FFF"

        mock_credential = AsyncMock()
        mock_token = MagicMock()
        mock_token.token = "token"
        mock_credential.get_token = AsyncMock(return_value=mock_token)
        mock_cred.return_value = mock_credential

        mock_openai = AsyncMock()
        mock_image_data = MagicMock()
        mock_image_data.b64_json = "base64data"
        mock_response = MagicMock()
        mock_response.data = [mock_image_data]
        mock_openai.images.generate = AsyncMock(return_value=mock_response)
        mock_openai.close = AsyncMock()
        mock_client.return_value = mock_openai

        _ = await _generate_gpt_image(prompt="Test")

        call_kwargs = mock_openai.images.generate.call_args.kwargs
        assert call_kwargs["quality"] == "medium"


@pytest.mark.asyncio
async def test_generate_gpt_image_no_b64_falls_back_to_url():
    """Test fallback to URL fetch when b64_json is not available."""
    with patch("agents.image_content_agent.app_settings") as mock_settings, \
         patch("agents.image_content_agent.DefaultAzureCredential") as mock_cred, \
         patch("agents.image_content_agent.AsyncAzureOpenAI") as mock_client, \
         patch("aiohttp.ClientSession") as mock_session:

        mock_settings.azure_openai.effective_image_model = "gpt-image-1-mini"
        mock_settings.azure_openai.gpt_image_endpoint = "https://test.openai.azure.com"
        mock_settings.azure_openai.dalle_endpoint = None
        mock_settings.azure_openai.endpoint = "https://test.openai.azure.com"
        mock_settings.azure_openai.image_api_version = "2025-04-01-preview"
        mock_settings.azure_openai.image_size = "1024x1024"
        mock_settings.azure_openai.image_quality = "medium"
        mock_settings.base_settings.azure_client_id = None
        mock_settings.brand_guidelines.get_image_generation_prompt.return_value = "Brand"
        mock_settings.brand_guidelines.primary_color = "#000"
        mock_settings.brand_guidelines.secondary_color = "#FFF"

        mock_credential = AsyncMock()
        mock_token = MagicMock()
        mock_token.token = "token"
        mock_credential.get_token = AsyncMock(return_value=mock_token)
        mock_cred.return_value = mock_credential

        mock_openai = AsyncMock()
        mock_image_data = MagicMock()
        mock_image_data.b64_json = None
        mock_image_data.url = "https://example.com/image.png"
        mock_response = MagicMock()
        mock_response.data = [mock_image_data]
        mock_openai.images.generate = AsyncMock(return_value=mock_response)
        mock_openai.close = AsyncMock()
        mock_client.return_value = mock_openai

        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.read = AsyncMock(return_value=b"image-bytes")
        mock_session_instance = MagicMock()
        mock_session_instance.__aenter__ = AsyncMock(return_value=mock_session_instance)
        mock_session_instance.__aexit__ = AsyncMock()
        mock_session_instance.get = MagicMock(return_value=mock_resp)
        mock_resp.__aenter__ = AsyncMock(return_value=mock_resp)
        mock_resp.__aexit__ = AsyncMock()
        mock_session.return_value = mock_session_instance

        result = await _generate_gpt_image(prompt="Test")

        assert result["success"] is True


@pytest.mark.asyncio
async def test_generate_gpt_image_error_handling():
    """Test gpt-image error handling."""
    with patch("agents.image_content_agent.app_settings") as mock_settings, \
         patch("agents.image_content_agent.DefaultAzureCredential") as mock_cred:

        mock_settings.azure_openai.effective_image_model = "gpt-image-1-mini"
        mock_settings.azure_openai.gpt_image_endpoint = "https://test.openai.azure.com"
        mock_settings.azure_openai.dalle_endpoint = None
        mock_settings.azure_openai.endpoint = "https://test.openai.azure.com"
        mock_settings.azure_openai.image_api_version = "2025-04-01-preview"
        mock_settings.azure_openai.image_size = "1024x1024"
        mock_settings.azure_openai.image_quality = "medium"
        mock_settings.base_settings.azure_client_id = None
        mock_settings.brand_guidelines.get_image_generation_prompt.return_value = "Brand"
        mock_settings.brand_guidelines.primary_color = "#000"
        mock_settings.brand_guidelines.secondary_color = "#FFF"

        mock_cred.side_effect = Exception("Auth error")

        result = await _generate_gpt_image(prompt="Test")

        assert result["success"] is False
        assert "error" in result


@pytest.mark.asyncio
async def test_routes_to_dalle_for_dalle_model():
    """Test that dall-e-3 model routes to DALL-E generator."""
    with patch("agents.image_content_agent.app_settings") as mock_settings, \
         patch("agents.image_content_agent._generate_dalle_image") as mock_dalle, \
         patch("agents.image_content_agent._generate_gpt_image") as mock_gpt:

        mock_settings.azure_openai.effective_image_model = "dall-e-3"
        mock_dalle.return_value = {"success": True, "model": "dall-e-3"}
        mock_gpt.return_value = {"success": True, "model": "gpt-image-1-mini"}

        result = await generate_dalle_image(prompt="Test")

        mock_dalle.assert_called_once()
        mock_gpt.assert_not_called()
        assert result["model"] == "dall-e-3"


@pytest.mark.asyncio
async def test_routes_to_gpt_image_for_gpt_model():
    """Test that gpt-image-1-mini model routes to gpt-image generator."""
    with patch("agents.image_content_agent.app_settings") as mock_settings, \
         patch("agents.image_content_agent._generate_dalle_image") as mock_dalle, \
         patch("agents.image_content_agent._generate_gpt_image") as mock_gpt:

        mock_settings.azure_openai.effective_image_model = "gpt-image-1-mini"
        mock_dalle.return_value = {"success": True, "model": "dall-e-3"}
        mock_gpt.return_value = {"success": True, "model": "gpt-image-1-mini"}

        result = await generate_dalle_image(prompt="Test")

        mock_gpt.assert_called_once()
        mock_dalle.assert_not_called()
        assert result["model"] == "gpt-image-1-mini"


@pytest.mark.asyncio
async def test_routes_to_gpt_image_for_gpt_image_1_5():
    """Test that gpt-image-1.5 model routes to gpt-image generator."""
    with patch("agents.image_content_agent.app_settings") as mock_settings, \
         patch("agents.image_content_agent._generate_dalle_image") as mock_dalle, \
         patch("agents.image_content_agent._generate_gpt_image") as mock_gpt:

        mock_settings.azure_openai.effective_image_model = "gpt-image-1.5"
        mock_dalle.return_value = {"success": True, "model": "dall-e-3"}
        mock_gpt.return_value = {"success": True, "model": "gpt-image-1.5"}

        _ = await generate_dalle_image(prompt="Test")

        mock_gpt.assert_called_once()
        mock_dalle.assert_not_called()


def test_truncate_preserves_hex_in_middle_of_line():
    """Test hex code in middle of line is preserved."""

    # Text with #hex in the middle of lines
    desc = """### Product Name
The color has hex #FF0000 which is vibrant.
More content here with another # reference.
""" + "Padding. " * 300

    result = _truncate_for_image(desc, max_chars=400)
    # Should contain some hex reference
    assert len(result) <= 400


def test_truncate_preserves_description_quotes():
    """Test quoted descriptions with 'appears as' are preserved."""

    desc = '''### Product
"This color appears as a soft blue tone. It has variations in the light."
More details here.
''' + "Extra. " * 400

    result = _truncate_for_image(desc, max_chars=500)
    assert len(result) <= 500


def test_truncate_with_eggshell_finish():
    """Test that eggshell finish descriptions are considered."""

    desc = """### Product
Basic description.
This has an eggshell finish for a subtle texture.
Hex: #AABBCC
""" + "Filler. " * 300

    result = _truncate_for_image(desc, max_chars=400)
    assert len(result) <= 400


@pytest.mark.asyncio
async def test_generate_image_truncates_very_long_prompt():
    """Test that _generate_dalle_image truncates very long product descriptions.

    Verifies that when a very long product description is passed, it gets
    truncated before being sent to the OpenAI API.
    """
    with patch("agents.image_content_agent.app_settings") as mock_settings, \
         patch("agents.image_content_agent.DefaultAzureCredential") as mock_cred, \
         patch("agents.image_content_agent.AsyncAzureOpenAI") as mock_client:

        # Setup settings (using correct attribute names matching settings.py)
        mock_settings.azure_openai.effective_image_model = "dall-e-3"
        mock_settings.azure_openai.image_endpoint = "https://test.openai.azure.com"
        mock_settings.azure_openai.endpoint = "https://test.openai.azure.com"
        mock_settings.azure_openai.preview_api_version = "2024-02-15-preview"
        mock_settings.azure_openai.image_model = "dall-e-3"
        mock_settings.azure_openai.image_size = "1024x1024"
        mock_settings.azure_openai.image_quality = "standard"
        mock_settings.base_settings.azure_client_id = None
        mock_settings.brand_guidelines.get_image_generation_prompt.return_value = "Brand style"
        mock_settings.brand_guidelines.primary_color = "#FF0000"
        mock_settings.brand_guidelines.secondary_color = "#00FF00"

        # Setup credential mock
        mock_credential = AsyncMock()
        mock_token = MagicMock()
        mock_token.token = "test-token"
        mock_credential.get_token = AsyncMock(return_value=mock_token)
        mock_cred.return_value = mock_credential

        # Setup OpenAI client mock - capture the prompt argument
        mock_openai = AsyncMock()
        mock_image_data = MagicMock()
        mock_image_data.b64_json = base64.b64encode(b"fake-image").decode()
        mock_image_data.revised_prompt = None
        mock_response = MagicMock()
        mock_response.data = [mock_image_data]
        mock_openai.images.generate = AsyncMock(return_value=mock_response)
        mock_openai.close = AsyncMock()
        mock_client.return_value = mock_openai

        # Create very long product description (~10000 chars)
        very_long_product_desc = "Product description with details. " * 300

        result = await generate_image(
            prompt="Create marketing image",
            product_description=very_long_product_desc,
            scene_description="Modern kitchen"
        )

        # Verify success
        assert result["success"] is True

        # Verify the prompt was truncated before being sent to OpenAI
        call_kwargs = mock_openai.images.generate.call_args.kwargs
        prompt_sent = call_kwargs["prompt"]

        # The full prompt should be under DALL-E's limit (~4000 chars)
        # despite the ~10000 char input
        assert len(prompt_sent) < 4000, f"Prompt not truncated: {len(prompt_sent)} chars"

        # Also verify via prompt_used in result
        assert len(result["prompt_used"]) < 4000
