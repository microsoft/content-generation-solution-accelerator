"""
Unit tests for application settings with logic.

Only tests settings that have computed properties, validators, or methods.
Simple field defaults are tested implicitly through integration tests.
"""

import os
from unittest.mock import patch

import pytest
from settings import parse_comma_separated


class TestParseCommaSeparated:
    """Tests for comma-separated string parsing utility."""

    def test_parse_simple_list(self):
        """Test parsing a simple comma-separated list."""
        result = parse_comma_separated("a, b, c")
        assert result == ["a", "b", "c"]

    def test_parse_with_spaces(self):
        """Test parsing with extra spaces."""
        result = parse_comma_separated("  item1  ,  item2  ,  item3  ")
        assert result == ["item1", "item2", "item3"]

    def test_parse_empty_string(self):
        """Test parsing empty string."""
        result = parse_comma_separated("")
        assert result == []

    def test_parse_single_item(self):
        """Test parsing single item."""
        result = parse_comma_separated("single")
        assert result == ["single"]

    def test_parse_non_string(self):
        """Test that non-string returns empty list."""
        result = parse_comma_separated(123)
        assert result == []

    def test_parse_with_empty_items(self):
        """Test parsing with empty items between commas."""
        result = parse_comma_separated("a,,b,  ,c")
        assert result == ["a", "b", "c"]


class TestAzureOpenAIImageProperties:
    """Tests for Azure OpenAI image-related properties."""

    def test_image_endpoint_with_gpt_image_endpoint(self):
        """Test image_endpoint returns gpt_image_endpoint when set."""
        from settings import _AzureOpenAISettings

        with patch.dict(os.environ, {
            "AZURE_OPENAI_ENDPOINT": "https://test.openai.azure.com",
            "AZURE_OPENAI_GPT_IMAGE_ENDPOINT": "https://gpt-image.openai.azure.com"
        }, clear=False):
            settings = _AzureOpenAISettings()
            assert settings.image_endpoint == "https://gpt-image.openai.azure.com"

    def test_image_endpoint_falls_back_to_main_endpoint(self):
        """Test image_endpoint falls back to main endpoint."""
        from settings import _AzureOpenAISettings

        with patch.dict(os.environ, {
            "AZURE_OPENAI_ENDPOINT": "https://test.openai.azure.com",
            "AZURE_OPENAI_GPT_IMAGE_ENDPOINT": "",  # Explicitly clear to test fallback
        }, clear=True):
            settings = _AzureOpenAISettings(_env_file=None)
            # When no GPT endpoint is set, falls back to main endpoint
            assert settings.image_endpoint == "https://test.openai.azure.com"

    def test_effective_image_model_returns_image_model(self):
        """Test effective_image_model returns image_model directly."""
        from settings import _AzureOpenAISettings

        with patch.dict(os.environ, {
            "AZURE_OPENAI_ENDPOINT": "https://test.openai.azure.com",
            "AZURE_OPENAI_IMAGE_MODEL": "gpt-image-1.5"
        }, clear=False):
            settings = _AzureOpenAISettings()
            assert settings.effective_image_model == "gpt-image-1.5"


class TestImageGenerationEnabled:
    """Tests for image_generation_enabled property logic."""

    def test_disabled_with_none_model(self):
        """Test disabled when model is 'none'."""
        from settings import _AzureOpenAISettings

        with patch.dict(os.environ, {
            "AZURE_OPENAI_ENDPOINT": "https://test.openai.azure.com",
            "AZURE_OPENAI_IMAGE_MODEL": "none"
        }, clear=False):
            settings = _AzureOpenAISettings()
            assert settings.image_generation_enabled is False

    def test_disabled_with_disabled_model(self):
        """Test disabled when model is 'disabled'."""
        from settings import _AzureOpenAISettings

        with patch.dict(os.environ, {
            "AZURE_OPENAI_ENDPOINT": "https://test.openai.azure.com",
            "AZURE_OPENAI_IMAGE_MODEL": "disabled"
        }, clear=False):
            settings = _AzureOpenAISettings()
            assert settings.image_generation_enabled is False

    def test_enabled_with_valid_model_and_endpoint(self):
        """Test enabled when model and endpoint are valid."""
        from settings import _AzureOpenAISettings

        with patch.dict(os.environ, {
            "AZURE_OPENAI_ENDPOINT": "https://test.openai.azure.com",
            "AZURE_OPENAI_IMAGE_MODEL": "gpt-image-1-mini"
        }, clear=False):
            settings = _AzureOpenAISettings()
            assert settings.image_generation_enabled is True


class TestAzureOpenAIEndpointValidator:
    """Tests for AzureOpenAI ensure_endpoint validator."""

    def test_raises_when_neither_endpoint_nor_resource(self):
        """Test ValueError raised when neither endpoint nor resource provided."""
        from settings import _AzureOpenAISettings

        # Use _env_file=None to disable .env file loading for this instance
        with patch.dict(os.environ, {
            "AZURE_OPENAI_ENDPOINT": "",
            "AZURE_OPENAI_RESOURCE": "",
        }, clear=True):
            with pytest.raises(ValueError, match="AZURE_OPENAI_ENDPOINT or AZURE_OPENAI_RESOURCE is required"):
                _AzureOpenAISettings(_env_file=None)

    def test_derives_endpoint_from_resource(self):
        """Test endpoint is derived from resource when endpoint not provided."""
        from settings import _AzureOpenAISettings

        # Use _env_file=None to disable .env file loading for this instance
        with patch.dict(os.environ, {
            "AZURE_OPENAI_RESOURCE": "my-openai-resource",
            "AZURE_OPENAI_ENDPOINT": "",  # Clear endpoint so it derives from resource
        }, clear=True):
            settings = _AzureOpenAISettings(_env_file=None)
            assert settings.endpoint == "https://my-openai-resource.openai.azure.com"


class TestAppSettingsValidatorExceptionHandling:
    """Tests for AppSettings validator exception handling."""

    def test_storage_exception_sets_blob_none(self):
        """Test _StorageSettings exception results in blob=None."""
        from settings import _AppSettings, _StorageSettings

        with patch.object(_StorageSettings, '__init__', side_effect=Exception("Storage error")):
            settings = _AppSettings()
            assert settings.blob is None

    def test_cosmos_exception_sets_cosmos_none(self):
        """Test _CosmosSettings exception results in cosmos=None."""
        from settings import _AppSettings, _CosmosSettings

        with patch.object(_CosmosSettings, '__init__', side_effect=Exception("Cosmos error")):
            settings = _AppSettings()
            assert settings.cosmos is None

    def test_search_exception_sets_search_none(self):
        """Test _SearchSettings exception results in search=None."""
        from settings import _AppSettings, _SearchSettings

        with patch.object(_SearchSettings, '__init__', side_effect=Exception("Search error")):
            settings = _AppSettings()
            assert settings.search is None

    def test_chat_history_exception_sets_chat_history_none(self):
        """Test _ChatHistorySettings exception results in chat_history=None."""
        from settings import _AppSettings, _ChatHistorySettings

        with patch.object(_ChatHistorySettings, '__init__', side_effect=Exception("ChatHistory error")):
            settings = _AppSettings()
            assert settings.chat_history is None


class TestBrandGuidelinesProperties:
    """Tests for brand guidelines computed properties."""

    def test_prohibited_words_parses_string(self):
        """Test prohibited_words property parses comma-separated string."""
        from settings import _BrandGuidelinesSettings

        with patch.dict(os.environ, {
            "BRAND_PROHIBITED_WORDS": "cheap, budget, discount"
        }, clear=False):
            guidelines = _BrandGuidelinesSettings()
            assert guidelines.prohibited_words == ["cheap", "budget", "discount"]

    def test_prohibited_words_empty_when_not_set(self):
        """Test prohibited_words returns empty list when not set."""
        from settings import _BrandGuidelinesSettings

        guidelines = _BrandGuidelinesSettings()
        assert guidelines.prohibited_words == []

    def test_required_disclosures_parses_string(self):
        """Test required_disclosures property parses comma-separated string."""
        from settings import _BrandGuidelinesSettings

        with patch.dict(os.environ, {
            "BRAND_REQUIRED_DISCLOSURES": "Terms apply, See store for details"
        }, clear=False):
            guidelines = _BrandGuidelinesSettings()
            assert guidelines.required_disclosures == ["Terms apply", "See store for details"]


class TestBrandGuidelinesPromptMethods:
    """Tests for brand guidelines prompt generation methods."""

    def test_get_compliance_prompt_includes_key_sections(self):
        """Test get_compliance_prompt includes required sections."""
        from settings import _BrandGuidelinesSettings

        guidelines = _BrandGuidelinesSettings()
        prompt = guidelines.get_compliance_prompt()

        assert "Brand Compliance Rules" in prompt
        assert "Voice and Tone" in prompt
        assert "Content Restrictions" in prompt
        assert "Responsible AI Guidelines" in prompt
        assert guidelines.tone in prompt
        assert guidelines.voice in prompt

    def test_get_text_generation_prompt_includes_key_sections(self):
        """Test get_text_generation_prompt includes required sections."""
        from settings import _BrandGuidelinesSettings

        guidelines = _BrandGuidelinesSettings()
        prompt = guidelines.get_text_generation_prompt()

        assert "Brand Voice Guidelines" in prompt
        assert "Writing Rules" in prompt
        assert "Responsible AI - Text Content Rules" in prompt
        assert str(guidelines.max_headline_length) in prompt
        assert str(guidelines.max_body_length) in prompt

    def test_get_image_generation_prompt_includes_key_sections(self):
        """Test get_image_generation_prompt includes required sections."""
        from settings import _BrandGuidelinesSettings

        guidelines = _BrandGuidelinesSettings()
        prompt = guidelines.get_image_generation_prompt()

        assert "MANDATORY: ZERO TEXT IN IMAGE" in prompt
        assert "Brand Visual Guidelines" in prompt
        assert "Color Accuracy" in prompt
        assert "Responsible AI - Image Generation Rules" in prompt
        assert guidelines.primary_color in prompt
        assert guidelines.secondary_color in prompt

    def test_get_text_generation_prompt_with_prohibited_words(self):
        """Test prompt includes prohibited words when set."""
        from settings import _BrandGuidelinesSettings

        with patch.dict(os.environ, {
            "BRAND_PROHIBITED_WORDS": "cheap,budget,discount"
        }, clear=False):
            guidelines = _BrandGuidelinesSettings()
            prompt = guidelines.get_text_generation_prompt()

            # Words should appear in the "NEVER use these words" section
            assert "cheap" in prompt
