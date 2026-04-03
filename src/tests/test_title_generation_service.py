"""
Unit tests for the Title Generation Service.

Tests cover:
- TitleService._fallback_title() static method
- TitleService.generate_title() with mocked AI agent
- get_title_service() singleton factory
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from services.title_service import TitleService, get_title_service


# ---------------------------------------------------------------------------
# _fallback_title  (static, no I/O)
# ---------------------------------------------------------------------------


class TestFallbackTitle:
    """Tests for the _fallback_title static method."""

    def test_returns_first_four_words(self):
        title = TitleService._fallback_title(
            "I need to create a social media post about paint products"
        )
        assert title == "I need to create"

    def test_short_message_uses_all_words(self):
        title = TitleService._fallback_title("Summer sale campaign")
        assert title == "Summer sale campaign"

    def test_empty_string_returns_default(self):
        assert TitleService._fallback_title("") == "New Conversation"

    def test_none_returns_default(self):
        assert TitleService._fallback_title(None) == "New Conversation"

    def test_whitespace_only_returns_default(self):
        assert TitleService._fallback_title("   ") == "New Conversation"

    def test_exactly_four_words(self):
        title = TitleService._fallback_title("Generate social media content")
        assert title == "Generate social media content"

    def test_strips_leading_trailing_whitespace(self):
        title = TitleService._fallback_title(
            "  Create a marketing campaign for holiday season  "
        )
        assert title == "Create a marketing campaign"


# ---------------------------------------------------------------------------
# generate_title  (AI agent mocked)
# ---------------------------------------------------------------------------


class TestGenerateTitle:
    """Tests for generate_title() with a mocked AI agent."""

    @pytest.fixture
    def title_service(self):
        """Create a TitleService with a mocked agent."""
        svc = TitleService()
        svc._agent = AsyncMock()
        svc._initialized = True
        return svc

    @pytest.mark.asyncio
    async def test_generates_clean_title(self, title_service):
        title_service._agent.run = AsyncMock(return_value="Paint Product Campaign")
        title = await title_service.generate_title(
            "I need to create a social media post about paint products for home renovation"
        )
        assert title == "Paint Product Campaign"

    @pytest.mark.asyncio
    async def test_removes_quotation_marks(self, title_service):
        title_service._agent.run = AsyncMock(return_value='"Social Media Post"')
        title = await title_service.generate_title("Create a social media post")
        assert title == "Social Media Post"

    @pytest.mark.asyncio
    async def test_removes_punctuation(self, title_service):
        title_service._agent.run = AsyncMock(return_value="Paint Products Campaign.")
        title = await title_service.generate_title("Post about paint products")
        assert title == "Paint Products Campaign"

    @pytest.mark.asyncio
    async def test_truncates_to_four_words(self, title_service):
        title_service._agent.run = AsyncMock(
            return_value="Social Media Marketing Campaign Strategy Plan"
        )
        title = await title_service.generate_title("Create a social media campaign")
        assert title == "Social Media Marketing Campaign"

    @pytest.mark.asyncio
    async def test_collapses_extra_whitespace(self, title_service):
        title_service._agent.run = AsyncMock(return_value="Paint   Product   Campaign")
        title = await title_service.generate_title("Paint products post")
        assert title == "Paint Product Campaign"

    @pytest.mark.asyncio
    async def test_multiline_response_uses_first_line(self, title_service):
        title_service._agent.run = AsyncMock(
            return_value="Paint Campaign\nThis is the title for the conversation"
        )
        title = await title_service.generate_title("Paint products")
        assert title == "Paint Campaign"

    @pytest.mark.asyncio
    async def test_empty_input_returns_default(self, title_service):
        title = await title_service.generate_title("")
        assert title == "New Conversation"
        title_service._agent.run.assert_not_called()

    @pytest.mark.asyncio
    async def test_none_input_returns_default(self, title_service):
        title = await title_service.generate_title(None)
        assert title == "New Conversation"
        title_service._agent.run.assert_not_called()

    @pytest.mark.asyncio
    async def test_agent_exception_uses_fallback(self, title_service):
        title_service._agent.run = AsyncMock(side_effect=Exception("API error"))
        title = await title_service.generate_title(
            "Create a social media post about summer sale"
        )
        assert title == "Create a social media"

    @pytest.mark.asyncio
    async def test_agent_empty_response_uses_fallback(self, title_service):
        title_service._agent.run = AsyncMock(return_value="")
        title = await title_service.generate_title(
            "Generate marketing copy for electronics"
        )
        assert title == "Generate marketing copy for"

    @pytest.mark.asyncio
    async def test_uninitialized_service_tries_initialize(self):
        svc = TitleService()
        svc._initialized = False
        svc._agent = None

        with patch.object(svc, "initialize") as mock_init:
            title = await svc.generate_title("Some message here today")
            mock_init.assert_called_once()
            # Agent still None → fallback
            assert title == "Some message here today"

    @pytest.mark.asyncio
    async def test_removes_backticks(self, title_service):
        title_service._agent.run = AsyncMock(return_value="`Social Media Campaign`")
        title = await title_service.generate_title("Social media campaign")
        assert title == "Social Media Campaign"


# ---------------------------------------------------------------------------
# get_title_service singleton
# ---------------------------------------------------------------------------


class TestGetTitleServiceSingleton:

    @patch("services.title_service._title_service", None)
    @patch("services.title_service.TitleService")
    def test_creates_new_instance_when_none(self, mock_cls):
        mock_instance = MagicMock()
        mock_cls.return_value = mock_instance
        result = get_title_service()
        mock_cls.assert_called_once()
        mock_instance.initialize.assert_called_once()
        assert result is mock_instance

    @patch("services.title_service._title_service")
    def test_returns_existing_instance(self, mock_existing):
        mock_existing.__bool__ = lambda self: True
        result = get_title_service()
        assert result is mock_existing
