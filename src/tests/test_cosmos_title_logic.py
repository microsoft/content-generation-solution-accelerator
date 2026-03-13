"""
Unit tests for the CosmosDB Service — conversation title-related logic.

Tests cover:
- add_message_to_conversation: generated_title handling
- save_conversation: metadata merging (preserving generated_title / custom_title)
- get_user_conversations: title resolution priority chain
- rename_conversation: custom_title overrides generated_title
- delete_all_conversations: bulk delete
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from services.cosmos_service import CosmosDBService


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_service(existing_conversation=None):
    """
    Return a CosmosDBService with Cosmos container mocked out.
    ``get_conversation`` returns *existing_conversation*.
    """
    svc = CosmosDBService()
    svc._client = MagicMock()                     # mark as initialised
    svc._conversations_container = AsyncMock()
    svc._conversations_container.upsert_item = AsyncMock(side_effect=lambda item: item)
    svc.get_conversation = AsyncMock(return_value=existing_conversation)
    svc.initialize = AsyncMock()
    return svc


# ===================================================================
# add_message_to_conversation
# ===================================================================


class TestAddMessageToConversation:

    @pytest.mark.asyncio
    async def test_new_conversation_stores_generated_title(self):
        svc = _make_service(existing_conversation=None)
        result = await svc.add_message_to_conversation(
            conversation_id="conv-1", user_id="u1",
            message={"role": "user", "content": "hello"},
            generated_title="Paint Campaign Post",
        )
        assert result["metadata"]["generated_title"] == "Paint Campaign Post"
        assert result["messages"] == [{"role": "user", "content": "hello"}]

    @pytest.mark.asyncio
    async def test_new_conversation_without_title(self):
        svc = _make_service(existing_conversation=None)
        result = await svc.add_message_to_conversation(
            conversation_id="conv-2", user_id="u1",
            message={"role": "user", "content": "hello"},
        )
        assert result["metadata"] == {}

    @pytest.mark.asyncio
    async def test_existing_sets_title_when_absent(self):
        existing = {
            "id": "conv-3", "userId": "u1",
            "messages": [{"role": "user", "content": "first"}],
            "metadata": {},
            "updated_at": "2025-01-01T00:00:00Z",
        }
        svc = _make_service(existing_conversation=existing)
        result = await svc.add_message_to_conversation(
            conversation_id="conv-3", user_id="u1",
            message={"role": "user", "content": "second"},
            generated_title="Paint Post",
        )
        assert result["metadata"]["generated_title"] == "Paint Post"
        assert len(result["messages"]) == 2

    @pytest.mark.asyncio
    async def test_does_not_overwrite_generated_title(self):
        existing = {
            "id": "conv-4", "userId": "u1",
            "messages": [{"role": "user", "content": "first"}],
            "metadata": {"generated_title": "Original Title"},
            "updated_at": "2025-01-01T00:00:00Z",
        }
        svc = _make_service(existing_conversation=existing)
        result = await svc.add_message_to_conversation(
            conversation_id="conv-4", user_id="u1",
            message={"role": "user", "content": "second"},
            generated_title="New Title Attempt",
        )
        assert result["metadata"]["generated_title"] == "Original Title"

    @pytest.mark.asyncio
    async def test_does_not_overwrite_custom_title(self):
        existing = {
            "id": "conv-5", "userId": "u1",
            "messages": [{"role": "user", "content": "first"}],
            "metadata": {"custom_title": "My Custom Name"},
            "updated_at": "2025-01-01T00:00:00Z",
        }
        svc = _make_service(existing_conversation=existing)
        result = await svc.add_message_to_conversation(
            conversation_id="conv-5", user_id="u1",
            message={"role": "user", "content": "second"},
            generated_title="AI Generated Title",
        )
        assert result["metadata"]["custom_title"] == "My Custom Name"
        assert "generated_title" not in result["metadata"]

    @pytest.mark.asyncio
    async def test_migrates_old_document_without_userId(self):
        existing = {
            "id": "conv-6", "user_id": "u1",
            "messages": [], "metadata": {},
            "updated_at": "2025-01-01T00:00:00Z",
        }
        svc = _make_service(existing_conversation=existing)
        result = await svc.add_message_to_conversation(
            conversation_id="conv-6", user_id="u1",
            message={"role": "user", "content": "hello"},
        )
        assert result["userId"] == "u1"


# ===================================================================
# save_conversation — metadata merging
# ===================================================================


class TestSaveConversationMetadataMerge:

    @pytest.mark.asyncio
    async def test_preserves_generated_title(self):
        existing = {
            "id": "cm1", "userId": "u1",
            "metadata": {"generated_title": "Paint Campaign"},
        }
        svc = _make_service(existing_conversation=existing)
        result = await svc.save_conversation(
            conversation_id="cm1", user_id="u1",
            messages=[{"role": "user", "content": "hi"}],
            metadata={"some_extra": "data"},
        )
        assert result["metadata"]["generated_title"] == "Paint Campaign"
        assert result["metadata"]["some_extra"] == "data"

    @pytest.mark.asyncio
    async def test_preserves_custom_title(self):
        existing = {
            "id": "cm2", "userId": "u1",
            "metadata": {"custom_title": "Renamed by user"},
        }
        svc = _make_service(existing_conversation=existing)
        result = await svc.save_conversation(
            conversation_id="cm2", user_id="u1",
            messages=[{"role": "user", "content": "x"}],
        )
        assert result["metadata"]["custom_title"] == "Renamed by user"

    @pytest.mark.asyncio
    async def test_new_conversation_empty_metadata(self):
        svc = _make_service(existing_conversation=None)
        result = await svc.save_conversation(
            conversation_id="cm3", user_id="u1", messages=[],
        )
        assert result["metadata"] == {}


# ===================================================================
# get_user_conversations — title resolution
# ===================================================================


class TestGetUserConversationsTitleResolution:

    @staticmethod
    def _make_query_service(items):
        svc = CosmosDBService()
        svc._client = MagicMock()
        svc.initialize = AsyncMock()

        async def _async_iter(*args, **kwargs):
            for item in items:
                yield item

        svc._conversations_container = MagicMock()
        svc._conversations_container.query_items = _async_iter
        return svc

    @pytest.mark.asyncio
    async def test_custom_title_wins(self):
        items = [{
            "id": "c1",
            "metadata": {"custom_title": "User Renamed", "generated_title": "AI Title"},
            "brief": {"overview": "Brief overview here"},
            "messages": [{"role": "user", "content": "Hello world"}],
            "updated_at": "2025-01-01",
        }]
        svc = self._make_query_service(items)
        result = await svc.get_user_conversations("u1")
        assert result[0]["title"] == "User Renamed"

    @pytest.mark.asyncio
    async def test_generated_title_wins_over_brief_and_message(self):
        items = [{
            "id": "c2",
            "metadata": {"generated_title": "Paint Campaign"},
            "brief": {"overview": "Summer Sale 2024 overview text"},
            "messages": [{"role": "user", "content": "social media post"}],
            "updated_at": "2025-01-01",
        }]
        svc = self._make_query_service(items)
        result = await svc.get_user_conversations("u1")
        assert result[0]["title"] == "Paint Campaign"

    @pytest.mark.asyncio
    async def test_brief_overview_fallback_four_words(self):
        items = [{
            "id": "c3", "metadata": {},
            "brief": {"overview": "Summer Sale 2024 Campaign overview text"},
            "messages": [], "updated_at": "2025-01-01",
        }]
        svc = self._make_query_service(items)
        result = await svc.get_user_conversations("u1")
        assert result[0]["title"] == "Summer Sale 2024 Campaign"

    @pytest.mark.asyncio
    async def test_first_user_message_fallback_four_words(self):
        items = [{
            "id": "c4", "metadata": {}, "brief": None,
            "messages": [
                {"role": "assistant", "content": "Welcome!"},
                {"role": "user", "content": "I need to create a social media post about paint"},
            ],
            "updated_at": "2025-01-01",
        }]
        svc = self._make_query_service(items)
        result = await svc.get_user_conversations("u1")
        assert result[0]["title"] == "I need to create"

    @pytest.mark.asyncio
    async def test_empty_conversation_default(self):
        items = [{
            "id": "c5", "metadata": {}, "brief": None,
            "messages": [], "updated_at": "2025-01-01",
        }]
        svc = self._make_query_service(items)
        result = await svc.get_user_conversations("u1")
        assert result[0]["title"] == "New Conversation"

    @pytest.mark.asyncio
    async def test_message_count_and_last_message(self):
        items = [{
            "id": "c6", "metadata": {"generated_title": "Test"}, "brief": None,
            "messages": [
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "How can I help?"},
            ],
            "updated_at": "2025-06-01",
        }]
        svc = self._make_query_service(items)
        result = await svc.get_user_conversations("u1")
        assert result[0]["messageCount"] == 2
        assert result[0]["lastMessage"] == "How can I help?"

    @pytest.mark.asyncio
    async def test_none_metadata_default(self):
        items = [{
            "id": "c7", "metadata": None, "brief": None,
            "messages": [], "updated_at": "2025-01-01",
        }]
        svc = self._make_query_service(items)
        result = await svc.get_user_conversations("u1")
        assert result[0]["title"] == "New Conversation"


# ===================================================================
# rename_conversation
# ===================================================================


class TestRenameConversation:

    @pytest.mark.asyncio
    async def test_sets_custom_title(self):
        existing = {
            "id": "cr1", "userId": "u1",
            "metadata": {"generated_title": "AI Generated"},
            "messages": [],
        }
        svc = _make_service(existing_conversation=existing)
        result = await svc.rename_conversation("cr1", "u1", "My Custom Name")
        assert result["metadata"]["custom_title"] == "My Custom Name"
        assert result["metadata"]["generated_title"] == "AI Generated"

    @pytest.mark.asyncio
    async def test_missing_conversation_returns_none(self):
        svc = _make_service(existing_conversation=None)
        result = await svc.rename_conversation("missing", "u1", "Name")
        assert result is None


# ===================================================================
# delete_all_conversations
# ===================================================================


class TestDeleteAllConversations:

    @pytest.mark.asyncio
    async def test_deletes_all_returns_count(self):
        convs = [{"id": "c1", "title": "a"}, {"id": "c2", "title": "b"}, {"id": "c3", "title": "c"}]
        svc = _make_service(existing_conversation=None)
        svc.get_user_conversations = AsyncMock(return_value=convs)
        svc.delete_conversation = AsyncMock(return_value=True)
        count = await svc.delete_all_conversations("u1")
        assert count == 3
        assert svc.delete_conversation.call_count == 3

    @pytest.mark.asyncio
    async def test_handles_partial_failures(self):
        convs = [{"id": "c1", "title": "a"}, {"id": "c2", "title": "b"}]
        svc = _make_service(existing_conversation=None)
        svc.get_user_conversations = AsyncMock(return_value=convs)
        svc.delete_conversation = AsyncMock(side_effect=[True, Exception("fail")])
        count = await svc.delete_all_conversations("u1")
        assert count == 1

    @pytest.mark.asyncio
    async def test_empty_history_returns_zero(self):
        svc = _make_service(existing_conversation=None)
        svc.get_user_conversations = AsyncMock(return_value=[])
        svc.delete_conversation = AsyncMock()
        count = await svc.delete_all_conversations("u1")
        assert count == 0
        svc.delete_conversation.assert_not_called()
