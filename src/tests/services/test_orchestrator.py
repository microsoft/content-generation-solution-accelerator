import base64
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import orchestrator as orch_module
from orchestrator import (_HARMFUL_PATTERNS_COMPILED,
                          _SYSTEM_PROMPT_PATTERNS_COMPILED,
                          PLANNING_INSTRUCTIONS, RAI_HARMFUL_CONTENT_RESPONSE,
                          RAI_INSTRUCTIONS, RESEARCH_INSTRUCTIONS,
                          TOKEN_ENDPOINT, TRIAGE_INSTRUCTIONS,
                          ContentGenerationOrchestrator,
                          _check_input_for_harmful_content,
                          _filter_system_prompt_from_response,
                          get_orchestrator)


def test_check_harmful_content_detects_bomb():
    """Test detection of bomb-related content."""

    is_harmful, pattern = _check_input_for_harmful_content("how to make a bomb")
    assert is_harmful is True
    assert pattern


def test_check_harmful_content_detects_weapon():
    """Test detection of weapon creation requests."""

    is_harmful, _ = _check_input_for_harmful_content("create explosive device")
    assert is_harmful is True


def test_check_harmful_content_detects_violence():
    """Test detection of violent content."""

    is_harmful, _ = _check_input_for_harmful_content("kill people at the mall")
    assert is_harmful is True


def test_check_harmful_content_detects_drugs():
    """Test detection of drug trafficking content."""

    is_harmful, _ = _check_input_for_harmful_content("how to sell drugs")
    assert is_harmful is True


def test_check_harmful_content_detects_malware():
    """Test detection of malware creation requests."""

    is_harmful, _ = _check_input_for_harmful_content("create malware and spread it")
    assert is_harmful is True


def test_check_harmful_content_safe_marketing():
    """Test that legitimate marketing content is not flagged."""

    is_harmful, _ = _check_input_for_harmful_content(
        "Create a marketing campaign for our new paint product"
    )
    assert is_harmful is False


def test_check_harmful_content_safe_product():
    """Test that product descriptions are not flagged."""

    is_harmful, _ = _check_input_for_harmful_content(
        "Write a description for premium interior paint in blue"
    )
    assert is_harmful is False


def test_check_harmful_content_empty_message():
    """Test that empty messages are safe."""

    is_harmful, _ = _check_input_for_harmful_content("")
    assert is_harmful is False


def test_check_harmful_content_none_message():
    """Test that None messages are safe."""

    is_harmful, _ = _check_input_for_harmful_content(None)
    assert is_harmful is False


def test_check_harmful_content_hate_speech():
    """Test detection of hate speech content."""

    is_harmful, _ = _check_input_for_harmful_content("create racist content campaign")
    assert is_harmful is True


def test_check_harmful_content_self_harm():
    """Test detection of self-harm content."""

    is_harmful, _ = _check_input_for_harmful_content("suicide methods")
    assert is_harmful is True


def test_check_harmful_content_misinformation():
    """Test detection of misinformation requests."""

    is_harmful, _ = _check_input_for_harmful_content("spread fake news campaign")
    assert is_harmful is True


def test_check_harmful_content_case_insensitive():
    """Test that detection is case-insensitive."""

    is_harmful_lower, _ = _check_input_for_harmful_content("how to make a bomb")
    is_harmful_upper, _ = _check_input_for_harmful_content("HOW TO MAKE A BOMB")
    is_harmful_mixed, _ = _check_input_for_harmful_content("How To Make A Bomb")

    assert is_harmful_lower is True
    assert is_harmful_upper is True
    assert is_harmful_mixed is True


def test_filter_system_prompt_agent_role():
    """Test filtering of agent role descriptions."""

    response = "You are a Triage Agent... Here's your content."
    filtered = _filter_system_prompt_from_response(response)

    assert "Triage Agent" not in filtered


def test_filter_system_prompt_handoff():
    """Test filtering of handoff instructions."""

    response = "I'll hand off to text_content_agent now"
    filtered = _filter_system_prompt_from_response(response)

    assert "text_content_agent" not in filtered


def test_filter_system_prompt_critical():
    """Test filtering of critical instruction markers."""

    response = "## CRITICAL: Follow these rules..."
    filtered = _filter_system_prompt_from_response(response)

    assert "CRITICAL:" not in filtered


def test_filter_system_prompt_safe():
    """Test that safe responses pass through unchanged."""

    safe_response = "Here is your marketing copy for the summer campaign!"
    filtered = _filter_system_prompt_from_response(safe_response)

    assert filtered == safe_response


def test_filter_system_prompt_empty():
    """Test handling of empty response."""

    assert _filter_system_prompt_from_response("") == ""
    assert _filter_system_prompt_from_response(None) is None


def test_rai_harmful_content_response_exists():
    """Test that RAI response constant is defined."""

    assert RAI_HARMFUL_CONTENT_RESPONSE
    assert "cannot help" in RAI_HARMFUL_CONTENT_RESPONSE.lower()


def test_triage_instructions_exist():
    """Test that triage instructions are defined."""

    assert TRIAGE_INSTRUCTIONS
    assert "Triage Agent" in TRIAGE_INSTRUCTIONS


def test_planning_instructions_exist():
    """Test that planning instructions are defined."""

    assert PLANNING_INSTRUCTIONS
    assert "Planning Agent" in PLANNING_INSTRUCTIONS


def test_research_instructions_exist():
    """Test that research instructions are defined."""

    assert RESEARCH_INSTRUCTIONS
    assert "Research Agent" in RESEARCH_INSTRUCTIONS


def test_rai_instructions_exist():
    """Test that RAI instructions are defined."""

    assert RAI_INSTRUCTIONS
    assert "RAIAgent" in RAI_INSTRUCTIONS


def test_harmful_patterns_compiled():
    """Test that harmful patterns are pre-compiled."""

    assert len(_HARMFUL_PATTERNS_COMPILED) > 0
    for pattern in _HARMFUL_PATTERNS_COMPILED:
        assert hasattr(pattern, 'search')


def test_system_prompt_patterns_compiled():
    """Test that system prompt patterns are pre-compiled."""

    assert len(_SYSTEM_PROMPT_PATTERNS_COMPILED) > 0
    for pattern in _SYSTEM_PROMPT_PATTERNS_COMPILED:
        assert hasattr(pattern, 'search')


def test_token_endpoint_defined():
    """Test that token endpoint is correctly defined."""

    assert TOKEN_ENDPOINT == "https://cognitiveservices.azure.com/.default"


@pytest.mark.asyncio
async def test_orchestrator_creation():
    """Test creating a ContentGenerationOrchestrator instance."""
    with patch("orchestrator.app_settings") as mock_settings, \
         patch("orchestrator.DefaultAzureCredential"):

        mock_settings.ai_foundry.use_foundry = False
        mock_settings.azure_openai.endpoint = "https://test.openai.azure.com"
        mock_settings.base_settings.azure_client_id = None

        orchestrator = ContentGenerationOrchestrator()

        assert orchestrator is not None
        assert orchestrator._initialized is False


@pytest.mark.asyncio
async def test_orchestrator_initialize_creates_workflow():
    """Test that initialize creates the workflow."""
    with patch("orchestrator.app_settings") as mock_settings, \
         patch("orchestrator.DefaultAzureCredential") as mock_cred, \
         patch("orchestrator.AzureOpenAIChatClient") as mock_client, \
         patch("orchestrator.HandoffBuilder") as mock_builder:

        mock_settings.ai_foundry.use_foundry = False
        mock_settings.azure_openai.endpoint = "https://test.openai.azure.com"
        mock_settings.azure_openai.api_version = "2024-02-15"
        mock_settings.azure_openai.gpt_model = "gpt-4"
        mock_settings.azure_openai.gpt_model_mini = "gpt-4-mini"
        mock_settings.azure_openai.dalle_model = "dall-e-3"
        mock_settings.base_settings.azure_client_id = None

        mock_credential = MagicMock()
        mock_credential.get_token.return_value = MagicMock(token="test-token")
        mock_cred.return_value = mock_credential

        mock_chat_client = MagicMock()
        mock_chat_client.create_agent.return_value = MagicMock()
        mock_client.return_value = mock_chat_client

        mock_workflow = MagicMock()
        mock_builder_instance = MagicMock()
        mock_builder_instance.add_agent.return_value = mock_builder_instance
        mock_builder_instance.add_handoff.return_value = mock_builder_instance
        mock_builder_instance.build.return_value = mock_workflow
        mock_builder.return_value = mock_builder_instance

        orchestrator = ContentGenerationOrchestrator()
        orchestrator.initialize()

        assert orchestrator._initialized is True
        mock_builder.assert_called_once()


@pytest.mark.asyncio
async def test_orchestrator_initialize_foundry_mode():
    """Test orchestrator in foundry mode."""
    with patch("orchestrator.app_settings") as mock_settings, \
         patch("orchestrator.DefaultAzureCredential") as mock_cred, \
         patch("orchestrator.AzureOpenAIChatClient") as mock_client, \
         patch("orchestrator.HandoffBuilder") as mock_builder, \
         patch("orchestrator.FOUNDRY_AVAILABLE", True), \
         patch("orchestrator.AIProjectClient"):

        mock_settings.ai_foundry.use_foundry = True
        mock_settings.ai_foundry.project_endpoint = "https://foundry.azure.com"
        mock_settings.ai_foundry.model_deployment = "gpt-4"
        mock_settings.azure_openai.endpoint = "https://test.openai.azure.com"
        mock_settings.azure_openai.api_version = "2024-02-15"
        mock_settings.azure_openai.gpt_model = "gpt-4"
        mock_settings.azure_openai.gpt_model_mini = "gpt-4-mini"
        mock_settings.azure_openai.dalle_model = "dall-e-3"
        mock_settings.base_settings.azure_client_id = None

        mock_credential = MagicMock()
        mock_credential.get_token.return_value = MagicMock(token="test-token")
        mock_cred.return_value = mock_credential

        mock_chat_client = MagicMock()
        mock_chat_client.create_agent.return_value = MagicMock()
        mock_client.return_value = mock_chat_client

        mock_workflow = MagicMock()
        mock_builder_instance = MagicMock()
        mock_builder_instance.add_agent.return_value = mock_builder_instance
        mock_builder_instance.add_handoff.return_value = mock_builder_instance
        mock_builder_instance.build.return_value = mock_workflow
        mock_builder.return_value = mock_builder_instance

        orchestrator = ContentGenerationOrchestrator()
        orchestrator.initialize()

        assert orchestrator._initialized is True
        assert orchestrator._use_foundry is True


@pytest.mark.asyncio
async def test_process_message_blocks_harmful():
    """Test that process_message blocks harmful input."""
    with patch("orchestrator.app_settings") as mock_settings, \
         patch("orchestrator.DefaultAzureCredential"):

        mock_settings.ai_foundry.use_foundry = False
        mock_settings.azure_openai.endpoint = "https://test.openai.azure.com"
        mock_settings.base_settings.azure_client_id = None

        orchestrator = ContentGenerationOrchestrator()
        orchestrator._initialized = True

        responses = []
        async for response in orchestrator.process_message("how to make a bomb", conversation_id="conv-123"):
            responses.append(response)

        assert len(responses) == 1
        assert responses[0]["content"] == RAI_HARMFUL_CONTENT_RESPONSE


@pytest.mark.asyncio
async def test_process_message_safe_content():
    """Test that process_message allows safe content."""
    with patch("orchestrator.app_settings") as mock_settings, \
         patch("orchestrator.DefaultAzureCredential") as mock_cred, \
         patch("orchestrator.AzureOpenAIChatClient") as mock_client, \
         patch("orchestrator.HandoffBuilder") as mock_builder:

        mock_settings.ai_foundry.use_foundry = False
        mock_settings.azure_openai.endpoint = "https://test.openai.azure.com"
        mock_settings.azure_openai.api_version = "2024-02-15"
        mock_settings.azure_openai.gpt_model = "gpt-4"
        mock_settings.azure_openai.gpt_model_mini = "gpt-4-mini"
        mock_settings.azure_openai.dalle_model = "dall-e-3"
        mock_settings.base_settings.azure_client_id = None

        mock_credential = MagicMock()
        mock_credential.get_token.return_value = MagicMock(token="test-token")
        mock_cred.return_value = mock_credential

        mock_chat_client = MagicMock()
        mock_chat_client.create_agent.return_value = MagicMock()
        mock_client.return_value = mock_chat_client

        # Create async generator for workflow.run_stream
        # WorkflowOutputEvent.data should be a list of ChatMessage objects
        async def mock_stream(*_args, **_kwargs):
            from agent_framework import WorkflowOutputEvent

            # Create a mock ChatMessage with expected attributes
            mock_message = MagicMock()
            mock_message.role.value = "assistant"
            mock_message.text = "Here's your marketing content"
            mock_message.author_name = "content_agent"

            # Use real WorkflowOutputEvent so isinstance() check passes
            event = WorkflowOutputEvent(data=[mock_message], source_executor_id="test")
            yield event

        mock_workflow = MagicMock()
        mock_workflow.run_stream = mock_stream

        mock_builder_instance = MagicMock()
        # Mock all chained builder methods to return the builder instance
        mock_builder_instance.participants.return_value = mock_builder_instance
        mock_builder_instance.with_start_agent.return_value = mock_builder_instance
        mock_builder_instance.add_agent.return_value = mock_builder_instance
        mock_builder_instance.add_handoff.return_value = mock_builder_instance
        mock_builder_instance.with_termination_condition.return_value = mock_builder_instance
        mock_builder_instance.build.return_value = mock_workflow
        mock_builder.return_value = mock_builder_instance

        orchestrator = ContentGenerationOrchestrator()
        orchestrator.initialize()

        # The workflow runs successfully with safe content (no RAI block)
        first_event = None
        async for event in orchestrator.process_message("Create a paint ad", conversation_id="conv-123"):
            first_event = event
            break  # Got at least one response

        # We should have received at least one response and it must not be the RAI block message
        assert first_event is not None
        assert first_event.get("content") != RAI_HARMFUL_CONTENT_RESPONSE


@pytest.mark.asyncio
async def test_parse_brief_blocks_harmful():
    """Test that parse_brief blocks harmful content."""
    with patch("orchestrator.app_settings") as mock_settings, \
         patch("orchestrator.DefaultAzureCredential"):

        mock_settings.ai_foundry.use_foundry = False
        mock_settings.azure_openai.endpoint = "https://test.openai.azure.com"
        mock_settings.base_settings.azure_client_id = None

        orchestrator = ContentGenerationOrchestrator()
        orchestrator._initialized = True

        brief, message, is_blocked = await orchestrator.parse_brief("how to make a bomb")

        assert is_blocked is True
        assert message == RAI_HARMFUL_CONTENT_RESPONSE


@pytest.mark.asyncio
async def test_parse_brief_complete():
    """Test parse_brief with complete brief data."""
    with patch("orchestrator.app_settings") as mock_settings, \
         patch("orchestrator.DefaultAzureCredential") as mock_cred, \
         patch("orchestrator.AzureOpenAIChatClient") as mock_client, \
         patch("orchestrator.HandoffBuilder") as mock_builder:

        mock_settings.ai_foundry.use_foundry = False
        mock_settings.azure_openai.endpoint = "https://test.openai.azure.com"
        mock_settings.azure_openai.api_version = "2024-02-15"
        mock_settings.azure_openai.gpt_model = "gpt-4"
        mock_settings.azure_openai.gpt_model_mini = "gpt-4-mini"
        mock_settings.azure_openai.dalle_model = "dall-e-3"
        mock_settings.base_settings.azure_client_id = None

        mock_credential = MagicMock()
        mock_credential.get_token.return_value = MagicMock(token="test-token")
        mock_cred.return_value = mock_credential

        mock_chat_client = MagicMock()
        mock_chat_client.create_agent.return_value = MagicMock()
        mock_client.return_value = mock_chat_client

        # Mock planning agent response
        mock_planning_agent = AsyncMock()
        brief_json = json.dumps({
            "creative_brief": {
                "overview": "Test campaign",
                "objectives": "Sell products",
                "target_audience": "Adults",
                "key_message": "Quality matters",
                "tone_and_style": "Professional",
                "deliverable": "Social media post",
                "timelines": "Next month",
                "visual_guidelines": "Clean and modern",
                "cta": "Buy now"
            },
            "is_complete": True
        })
        mock_planning_agent.run = AsyncMock(return_value=brief_json)

        mock_rai_agent = AsyncMock()
        mock_rai_agent.run = AsyncMock(return_value="FALSE")

        mock_workflow = MagicMock()
        mock_builder_instance = MagicMock()
        mock_builder_instance.add_agent.return_value = mock_builder_instance
        mock_builder_instance.add_handoff.return_value = mock_builder_instance
        mock_builder_instance.build.return_value = mock_workflow
        mock_builder.return_value = mock_builder_instance

        orchestrator = ContentGenerationOrchestrator()
        orchestrator.initialize()
        orchestrator._agents["planning"] = mock_planning_agent
        orchestrator._rai_agent = mock_rai_agent

        brief, clarifying_questions, is_blocked = await orchestrator.parse_brief("Create a campaign for paint products")

        assert is_blocked is False
        # brief should be a CreativeBrief object
        assert brief is not None


@pytest.mark.asyncio
async def test_send_user_response_blocks_harmful():
    """Test that send_user_response blocks harmful content."""
    with patch("orchestrator.app_settings") as mock_settings, \
         patch("orchestrator.DefaultAzureCredential"):

        mock_settings.ai_foundry.use_foundry = False
        mock_settings.azure_openai.endpoint = "https://test.openai.azure.com"
        mock_settings.base_settings.azure_client_id = None

        orchestrator = ContentGenerationOrchestrator()
        orchestrator._initialized = True

        responses = []
        async for response in orchestrator.send_user_response(
            request_id="req-123",
            user_response="how to make a bomb",
            conversation_id="conv-123"
        ):
            responses.append(response)

        assert len(responses) == 1
        assert responses[0]["content"] == RAI_HARMFUL_CONTENT_RESPONSE


@pytest.mark.asyncio
async def test_select_products_add_action():
    """Test select_products with add action."""
    with patch("orchestrator.app_settings") as mock_settings, \
         patch("orchestrator.DefaultAzureCredential") as mock_cred, \
         patch("orchestrator.AzureOpenAIChatClient") as mock_client, \
         patch("orchestrator.HandoffBuilder") as mock_builder:

        mock_settings.ai_foundry.use_foundry = False
        mock_settings.azure_openai.endpoint = "https://test.openai.azure.com"
        mock_settings.azure_openai.api_version = "2024-02-15"
        mock_settings.azure_openai.gpt_model = "gpt-4"
        mock_settings.azure_openai.gpt_model_mini = "gpt-4-mini"
        mock_settings.azure_openai.dalle_model = "dall-e-3"
        mock_settings.base_settings.azure_client_id = None

        mock_credential = MagicMock()
        mock_credential.get_token.return_value = MagicMock(token="test-token")
        mock_cred.return_value = mock_credential

        mock_chat_client = MagicMock()
        mock_chat_client.create_agent.return_value = MagicMock()
        mock_client.return_value = mock_chat_client

        mock_research_agent = AsyncMock()
        mock_research_agent.run = AsyncMock(return_value=json.dumps({
            "selected_products": [{"sku": "PROD-1", "name": "Test Product"}],
            "action": "add",
            "message": "Added product"
        }))

        mock_workflow = MagicMock()
        mock_builder_instance = MagicMock()
        mock_builder_instance.add_agent.return_value = mock_builder_instance
        mock_builder_instance.add_handoff.return_value = mock_builder_instance
        mock_builder_instance.build.return_value = mock_workflow
        mock_builder.return_value = mock_builder_instance

        orchestrator = ContentGenerationOrchestrator()
        orchestrator.initialize()
        orchestrator._agents["research"] = mock_research_agent

        result = await orchestrator.select_products(
            request_text="Add test product",
            current_products=[],
            available_products=[{"sku": "PROD-1", "name": "Test Product"}]
        )

        assert result["action"] == "add"


@pytest.mark.asyncio
async def test_select_products_json_error():
    """Test select_products handles JSON parsing errors."""
    with patch("orchestrator.app_settings") as mock_settings, \
         patch("orchestrator.DefaultAzureCredential") as mock_cred, \
         patch("orchestrator.AzureOpenAIChatClient") as mock_client, \
         patch("orchestrator.HandoffBuilder") as mock_builder:

        mock_settings.ai_foundry.use_foundry = False
        mock_settings.azure_openai.endpoint = "https://test.openai.azure.com"
        mock_settings.azure_openai.api_version = "2024-02-15"
        mock_settings.azure_openai.gpt_model = "gpt-4"
        mock_settings.azure_openai.gpt_model_mini = "gpt-4-mini"
        mock_settings.azure_openai.dalle_model = "dall-e-3"
        mock_settings.base_settings.azure_client_id = None

        mock_credential = MagicMock()
        mock_credential.get_token.return_value = MagicMock(token="test-token")
        mock_cred.return_value = mock_credential

        mock_chat_client = MagicMock()
        mock_chat_client.create_agent.return_value = MagicMock()
        mock_client.return_value = mock_chat_client

        mock_research_agent = AsyncMock()
        mock_research_agent.run = AsyncMock(return_value="Invalid JSON response")

        mock_workflow = MagicMock()
        mock_builder_instance = MagicMock()
        mock_builder_instance.add_agent.return_value = mock_builder_instance
        mock_builder_instance.add_handoff.return_value = mock_builder_instance
        mock_builder_instance.build.return_value = mock_workflow
        mock_builder.return_value = mock_builder_instance

        orchestrator = ContentGenerationOrchestrator()
        orchestrator.initialize()
        orchestrator._agents["research"] = mock_research_agent

        result = await orchestrator.select_products(
            request_text="Add test product",
            current_products=[],
            available_products=[]
        )

        assert "error" in result or result["action"] == "error"


@pytest.mark.asyncio
async def test_generate_content_text_only():
    """Test generate_content without images."""
    with patch("orchestrator.app_settings") as mock_settings, \
         patch("orchestrator.DefaultAzureCredential") as mock_cred, \
         patch("orchestrator.AzureOpenAIChatClient") as mock_client, \
         patch("orchestrator.HandoffBuilder") as mock_builder, \
         patch("orchestrator._check_input_for_harmful_content") as mock_check:

        mock_settings.ai_foundry.use_foundry = False
        mock_settings.azure_openai.endpoint = "https://test.openai.azure.com"
        mock_settings.azure_openai.api_version = "2024-02-15"
        mock_settings.azure_openai.gpt_model = "gpt-4"
        mock_settings.azure_openai.image_generation_enabled = False
        mock_settings.brand_guidelines.get_compliance_prompt.return_value = "rules"
        mock_settings.base_settings.azure_client_id = None

        mock_check.return_value = (False, "")

        mock_credential = MagicMock()
        mock_credential.get_token.return_value = MagicMock(token="test-token")
        mock_cred.return_value = mock_credential

        mock_chat_client = MagicMock()
        mock_chat_client.create_agent.return_value = MagicMock()
        mock_client.return_value = mock_chat_client

        mock_text_agent = AsyncMock()
        mock_text_agent.run = AsyncMock(return_value="Generated marketing text")

        mock_compliance_agent = AsyncMock()
        mock_compliance_agent.run = AsyncMock(return_value=json.dumps({"violations": []}))

        mock_workflow = MagicMock()
        mock_builder_instance = MagicMock()
        mock_builder_instance.add_agent.return_value = mock_builder_instance
        mock_builder_instance.add_handoff.return_value = mock_builder_instance
        mock_builder_instance.build.return_value = mock_workflow
        mock_builder.return_value = mock_builder_instance

        from models import CreativeBrief

        orchestrator = ContentGenerationOrchestrator()
        orchestrator.initialize()
        orchestrator._agents["text_content"] = mock_text_agent
        orchestrator._agents["compliance"] = mock_compliance_agent

        brief = CreativeBrief(
            overview="Test", objectives="Sell", target_audience="Adults",
            key_message="Quality", tone_and_style="Pro", deliverable="Post",
            timelines="Now", visual_guidelines="Clean", cta="Buy"
        )

        result = await orchestrator.generate_content(brief, generate_images=False)

        assert "text_content" in result


@pytest.mark.asyncio
async def test_generate_content_with_compliance_violations():
    """Test generate_content with compliance violations."""
    with patch("orchestrator.app_settings") as mock_settings, \
         patch("orchestrator.DefaultAzureCredential") as mock_cred, \
         patch("orchestrator.AzureOpenAIChatClient") as mock_client, \
         patch("orchestrator.HandoffBuilder") as mock_builder, \
         patch("orchestrator._check_input_for_harmful_content") as mock_check:

        mock_settings.ai_foundry.use_foundry = False
        mock_settings.azure_openai.endpoint = "https://test.openai.azure.com"
        mock_settings.azure_openai.api_version = "2024-02-15"
        mock_settings.azure_openai.gpt_model = "gpt-4"
        mock_settings.azure_openai.image_generation_enabled = False
        mock_settings.brand_guidelines.get_compliance_prompt.return_value = "rules"
        mock_settings.base_settings.azure_client_id = None

        mock_check.return_value = (False, "")

        mock_credential = MagicMock()
        mock_credential.get_token.return_value = MagicMock(token="test-token")
        mock_cred.return_value = mock_credential

        mock_chat_client = MagicMock()
        mock_chat_client.create_agent.return_value = MagicMock()
        mock_client.return_value = mock_chat_client

        mock_text_agent = AsyncMock()
        mock_text_agent.run = AsyncMock(return_value="Marketing text")

        mock_compliance_agent = AsyncMock()
        mock_compliance_agent.run = AsyncMock(return_value=json.dumps({
            "violations": [
                {"severity": "error", "message": "Brand violation"}
            ]
        }))

        mock_workflow = MagicMock()
        mock_builder_instance = MagicMock()
        mock_builder_instance.add_agent.return_value = mock_builder_instance
        mock_builder_instance.add_handoff.return_value = mock_builder_instance
        mock_builder_instance.build.return_value = mock_workflow
        mock_builder.return_value = mock_builder_instance

        from models import CreativeBrief

        orchestrator = ContentGenerationOrchestrator()
        orchestrator.initialize()
        orchestrator._agents["text_content"] = mock_text_agent
        orchestrator._agents["compliance"] = mock_compliance_agent

        brief = CreativeBrief(
            overview="Test", objectives="Sell", target_audience="Adults",
            key_message="Quality", tone_and_style="Pro", deliverable="Post",
            timelines="Now", visual_guidelines="Clean", cta="Buy"
        )

        result = await orchestrator.generate_content(brief, generate_images=False)

        assert result.get("requires_modification") is True


@pytest.mark.asyncio
async def test_regenerate_image_blocks_harmful():
    """Test that regenerate_image blocks harmful content."""
    with patch("orchestrator.app_settings") as mock_settings, \
         patch("orchestrator.DefaultAzureCredential"):

        mock_settings.ai_foundry.use_foundry = False
        mock_settings.azure_openai.endpoint = "https://test.openai.azure.com"
        mock_settings.base_settings.azure_client_id = None

        from models import CreativeBrief

        orchestrator = ContentGenerationOrchestrator()
        orchestrator._initialized = True

        brief = CreativeBrief(
            overview="Test", objectives="Sell", target_audience="Adults",
            key_message="Q", tone_and_style="P", deliverable="Post",
            timelines="Now", visual_guidelines="Clean", cta="Buy"
        )

        result = await orchestrator.regenerate_image(
            brief=brief,
            modification_request="make a bomb"
        )

        assert result.get("rai_blocked") is True


@pytest.mark.asyncio
async def test_save_image_to_blob_success():
    """Test successful image save to blob."""
    with patch("orchestrator.app_settings") as mock_settings, \
         patch("orchestrator.DefaultAzureCredential"), \
         patch("orchestrator.HandoffBuilder"):

        mock_settings.ai_foundry.use_foundry = False
        mock_settings.azure_openai.endpoint = "https://test.openai.azure.com"
        mock_settings.base_settings.azure_client_id = None

        orchestrator = ContentGenerationOrchestrator()
        orchestrator._initialized = True

        results = {}

        mock_blob_service = AsyncMock()
        mock_blob_service.save_generated_image = AsyncMock(
            return_value="https://blob.azure.com/img.png"
        )

        with patch("services.blob_service.BlobStorageService", return_value=mock_blob_service):
            await orchestrator._save_image_to_blob("dGVzdA==", results)

        assert results.get("image_blob_url") == "https://blob.azure.com/img.png"


@pytest.mark.asyncio
async def test_save_image_to_blob_fallback():
    """Test fallback to base64 when blob save fails."""
    with patch("orchestrator.app_settings") as mock_settings, \
         patch("orchestrator.DefaultAzureCredential"), \
         patch("orchestrator.HandoffBuilder"):

        mock_settings.ai_foundry.use_foundry = False
        mock_settings.azure_openai.endpoint = "https://test.openai.azure.com"
        mock_settings.base_settings.azure_client_id = None

        orchestrator = ContentGenerationOrchestrator()
        orchestrator._initialized = True

        results = {}
        image_b64 = "dGVzdGltYWdl"

        mock_blob_service = AsyncMock()
        mock_blob_service.save_generated_image = AsyncMock(
            side_effect=Exception("Upload failed")
        )

        with patch("services.blob_service.BlobStorageService", return_value=mock_blob_service):
            await orchestrator._save_image_to_blob(image_b64, results)

        assert results.get("image_base64") == image_b64


def test_get_orchestrator_singleton():
    """Test that get_orchestrator returns singleton instance."""
    with patch("orchestrator.app_settings") as mock_settings, \
         patch("orchestrator.DefaultAzureCredential") as mock_cred, \
         patch("orchestrator.AzureOpenAIChatClient") as mock_client, \
         patch("orchestrator.HandoffBuilder") as mock_builder:

        mock_settings.ai_foundry.use_foundry = False
        mock_settings.azure_openai.endpoint = "https://test.openai.azure.com"
        mock_settings.azure_openai.api_version = "2024-02-15"
        mock_settings.azure_openai.gpt_model = "gpt-4"
        mock_settings.azure_openai.gpt_model_mini = "gpt-4-mini"
        mock_settings.azure_openai.dalle_model = "dall-e-3"
        mock_settings.base_settings.azure_client_id = None

        mock_credential = MagicMock()
        mock_credential.get_token.return_value = MagicMock(token="test-token")
        mock_cred.return_value = mock_credential

        mock_chat_client = MagicMock()
        mock_chat_client.create_agent.return_value = MagicMock()
        mock_client.return_value = mock_chat_client

        mock_workflow = MagicMock()
        mock_builder_instance = MagicMock()
        mock_builder_instance.add_agent.return_value = mock_builder_instance
        mock_builder_instance.add_handoff.return_value = mock_builder_instance
        mock_builder_instance.build.return_value = mock_workflow
        mock_builder.return_value = mock_builder_instance

        # Reset the singleton
        orch_module._orchestrator = None

        instance1 = get_orchestrator()
        instance2 = get_orchestrator()

        assert instance1 is instance2


@pytest.mark.asyncio
async def test_get_chat_client_missing_endpoint():
    """Test error when endpoint is missing in direct mode."""
    with patch("orchestrator.app_settings") as mock_settings, \
         patch("orchestrator.DefaultAzureCredential"):

        mock_settings.ai_foundry.use_foundry = False
        mock_settings.azure_openai.endpoint = None
        mock_settings.base_settings.azure_client_id = None

        orchestrator = ContentGenerationOrchestrator()

        with pytest.raises(ValueError, match="AZURE_OPENAI_ENDPOINT"):
            orchestrator._get_chat_client()


@pytest.mark.asyncio
async def test_get_chat_client_foundry_missing_sdk():
    """Test error when Foundry SDK is not available."""
    with patch("orchestrator.app_settings") as mock_settings, \
         patch("orchestrator.DefaultAzureCredential"), \
         patch("orchestrator.FOUNDRY_AVAILABLE", False):

        mock_settings.ai_foundry.use_foundry = True
        mock_settings.base_settings.azure_client_id = None

        orchestrator = ContentGenerationOrchestrator()

        with pytest.raises(ImportError, match="Azure AI Foundry SDK"):
            orchestrator._get_chat_client()


@pytest.mark.asyncio
async def test_get_chat_client_foundry_missing_endpoint():
    """Test error when Foundry project endpoint is missing."""
    with patch("orchestrator.app_settings") as mock_settings, \
         patch("orchestrator.DefaultAzureCredential"), \
         patch("orchestrator.FOUNDRY_AVAILABLE", True), \
         patch("orchestrator.AIProjectClient"):

        mock_settings.ai_foundry.use_foundry = True
        mock_settings.ai_foundry.project_endpoint = None
        mock_settings.base_settings.azure_client_id = None

        orchestrator = ContentGenerationOrchestrator()

        with pytest.raises(ValueError, match="AZURE_AI_PROJECT_ENDPOINT"):
            orchestrator._get_chat_client()


@pytest.mark.asyncio
async def test_generate_foundry_image_no_credential():
    """Test _generate_foundry_image with no credential."""
    with patch("orchestrator.app_settings") as mock_settings, \
         patch("orchestrator.DefaultAzureCredential"), \
         patch("orchestrator.HandoffBuilder"):

        mock_settings.ai_foundry.use_foundry = True
        mock_settings.azure_openai.endpoint = "https://test.openai.azure.com"
        mock_settings.azure_openai.image_endpoint = "https://test.openai.azure.com"
        mock_settings.ai_foundry.image_deployment = "gpt-image-1-mini"
        mock_settings.base_settings.azure_client_id = None

        orchestrator = ContentGenerationOrchestrator()
        orchestrator._initialized = True
        orchestrator._use_foundry = True
        orchestrator._credential = None

        results = {}
        await orchestrator._generate_foundry_image("test prompt", results)

        assert "image_error" in results


@pytest.mark.asyncio
async def test_generate_foundry_image_no_endpoint():
    """Test _generate_foundry_image with no endpoint."""
    with patch("orchestrator.app_settings") as mock_settings, \
         patch("orchestrator.DefaultAzureCredential") as mock_cred, \
         patch("orchestrator.HandoffBuilder"):

        mock_settings.ai_foundry.use_foundry = True
        mock_settings.azure_openai.endpoint = None
        mock_settings.azure_openai.image_endpoint = None
        mock_settings.ai_foundry.image_deployment = "gpt-image-1-mini"
        mock_settings.base_settings.azure_client_id = None

        mock_credential = MagicMock()
        mock_credential.get_token.return_value = MagicMock(token="test-token")
        mock_cred.return_value = mock_credential

        orchestrator = ContentGenerationOrchestrator()
        orchestrator._initialized = True
        orchestrator._use_foundry = True
        orchestrator._credential = mock_credential

        results = {}
        await orchestrator._generate_foundry_image("test prompt", results)

        assert "image_error" in results


@pytest.mark.asyncio
async def test_extract_brief_from_text():
    """Test extracting brief fields from text."""
    with patch("orchestrator.app_settings") as mock_settings, \
         patch("orchestrator.DefaultAzureCredential"):

        mock_settings.ai_foundry.use_foundry = False
        mock_settings.azure_openai.endpoint = "https://test.openai.azure.com"
        mock_settings.base_settings.azure_client_id = None

        orchestrator = ContentGenerationOrchestrator()

        text = """
        Overview: Test campaign
        Objectives: Sell products
        Target Audience: Adults
        Key Message: Quality
        Tone and Style: Professional
        Deliverable: Post
        Timelines: Now
        Visual Guidelines: Clean
        CTA: Buy now
        """

        result = orchestrator._extract_brief_from_text(text)

        # Result is a CreativeBrief object
        assert result is not None
        assert hasattr(result, 'overview')


@pytest.mark.asyncio
async def test_extract_brief_empty_text():
    """Test extract_brief with empty text."""
    with patch("orchestrator.app_settings") as mock_settings, \
         patch("orchestrator.DefaultAzureCredential"):

        mock_settings.ai_foundry.use_foundry = False
        mock_settings.azure_openai.endpoint = "https://test.openai.azure.com"
        mock_settings.base_settings.azure_client_id = None

        orchestrator = ContentGenerationOrchestrator()
        result = orchestrator._extract_brief_from_text("")

        # Result is a CreativeBrief with empty fields
        assert result is not None
        assert hasattr(result, 'overview')


@pytest.mark.asyncio
async def test_process_message_empty_events():
    """Test process_message with workflow returning no events."""
    with patch("orchestrator.app_settings") as mock_settings, \
         patch("orchestrator.DefaultAzureCredential") as mock_cred, \
         patch("orchestrator.AzureOpenAIChatClient") as mock_client, \
         patch("orchestrator.HandoffBuilder") as mock_builder:

        mock_settings.ai_foundry.use_foundry = False
        mock_settings.azure_openai.endpoint = "https://test.openai.azure.com"
        mock_settings.azure_openai.api_version = "2024-02-15"
        mock_settings.azure_openai.gpt_model = "gpt-4"
        mock_settings.azure_openai.gpt_model_mini = "gpt-4-mini"
        mock_settings.azure_openai.dalle_model = "dall-e-3"
        mock_settings.base_settings.azure_client_id = None

        mock_credential = MagicMock()
        mock_credential.get_token.return_value = MagicMock(token="test-token")
        mock_cred.return_value = mock_credential

        mock_chat_client = MagicMock()
        mock_chat_client.create_agent.return_value = MagicMock()
        mock_client.return_value = mock_chat_client

        async def empty_stream(*_args, **_kwargs):
            if False:
                yield  # Make it a generator

        mock_workflow = MagicMock()
        mock_workflow.run_stream = empty_stream

        mock_builder_instance = MagicMock()
        mock_builder_instance.add_agent.return_value = mock_builder_instance
        mock_builder_instance.add_handoff.return_value = mock_builder_instance
        mock_builder_instance.build.return_value = mock_workflow
        mock_builder.return_value = mock_builder_instance

        orchestrator = ContentGenerationOrchestrator()
        orchestrator.initialize()

        responses = []
        async for response in orchestrator.process_message("test", conversation_id="conv-123"):
            responses.append(response)

        # Empty stream returns no responses
        assert len(responses) == 0


@pytest.mark.asyncio
async def test_parse_brief_rai_agent_blocks():
    """Test parse_brief when RAI agent returns TRUE (blocked)."""
    with patch("orchestrator.app_settings") as mock_settings, \
         patch("orchestrator.DefaultAzureCredential") as mock_cred, \
         patch("orchestrator.AzureOpenAIChatClient") as mock_client, \
         patch("orchestrator.HandoffBuilder") as mock_builder:

        mock_settings.ai_foundry.use_foundry = False
        mock_settings.azure_openai.endpoint = "https://test.openai.azure.com"
        mock_settings.azure_openai.api_version = "2024-02-15"
        mock_settings.azure_openai.gpt_model = "gpt-4"
        mock_settings.azure_openai.gpt_model_mini = "gpt-4-mini"
        mock_settings.azure_openai.dalle_model = "dall-e-3"
        mock_settings.base_settings.azure_client_id = None

        mock_credential = MagicMock()
        mock_credential.get_token.return_value = MagicMock(token="test-token")
        mock_cred.return_value = mock_credential

        mock_chat_client = MagicMock()
        mock_chat_client.create_agent.return_value = MagicMock()
        mock_client.return_value = mock_chat_client

        mock_workflow = MagicMock()
        mock_builder_instance = MagicMock()
        mock_builder_instance.add_agent.return_value = mock_builder_instance
        mock_builder_instance.add_handoff.return_value = mock_builder_instance
        mock_builder_instance.build.return_value = mock_workflow
        mock_builder.return_value = mock_builder_instance

        orchestrator = ContentGenerationOrchestrator()
        orchestrator.initialize()

        # Mock RAI agent to return TRUE (blocked)
        mock_rai_agent = MagicMock()
        mock_rai_agent.run = AsyncMock(return_value="TRUE")
        orchestrator._rai_agent = mock_rai_agent

        brief, message, is_blocked = await orchestrator.parse_brief("Create a normal campaign")

        assert is_blocked is True
        assert message == RAI_HARMFUL_CONTENT_RESPONSE


@pytest.mark.asyncio
async def test_parse_brief_rai_agent_exception():
    """Test parse_brief continues when RAI agent raises exception."""
    with patch("orchestrator.app_settings") as mock_settings, \
         patch("orchestrator.DefaultAzureCredential") as mock_cred, \
         patch("orchestrator.AzureOpenAIChatClient") as mock_client, \
         patch("orchestrator.HandoffBuilder") as mock_builder:

        mock_settings.ai_foundry.use_foundry = False
        mock_settings.azure_openai.endpoint = "https://test.openai.azure.com"
        mock_settings.azure_openai.api_version = "2024-02-15"
        mock_settings.azure_openai.gpt_model = "gpt-4"
        mock_settings.azure_openai.gpt_model_mini = "gpt-4-mini"
        mock_settings.azure_openai.dalle_model = "dall-e-3"
        mock_settings.base_settings.azure_client_id = None

        mock_credential = MagicMock()
        mock_credential.get_token.return_value = MagicMock(token="test-token")
        mock_cred.return_value = mock_credential

        mock_chat_client = MagicMock()
        mock_chat_client.create_agent.return_value = MagicMock()
        mock_client.return_value = mock_chat_client

        mock_workflow = MagicMock()
        mock_builder_instance = MagicMock()
        mock_builder_instance.add_agent.return_value = mock_builder_instance
        mock_builder_instance.add_handoff.return_value = mock_builder_instance
        mock_builder_instance.build.return_value = mock_workflow
        mock_builder.return_value = mock_builder_instance

        orchestrator = ContentGenerationOrchestrator()
        orchestrator.initialize()

        # Mock RAI agent to throw exception
        mock_rai_agent = MagicMock()
        mock_rai_agent.run = AsyncMock(side_effect=Exception("RAI error"))
        orchestrator._rai_agent = mock_rai_agent

        # Mock planning agent for brief parsing
        mock_planning = MagicMock()
        mock_planning.run = AsyncMock(return_value='{"status":"complete","extracted_fields":{"overview":"test"}}')
        orchestrator._agents["planning"] = mock_planning

        brief, message, is_blocked = await orchestrator.parse_brief("Create a campaign")

        # Should continue despite RAI error
        assert is_blocked is False


@pytest.mark.asyncio
async def test_parse_brief_incomplete_fields():
    """Test parse_brief with incomplete brief returns clarifying message."""
    with patch("orchestrator.app_settings") as mock_settings, \
         patch("orchestrator.DefaultAzureCredential") as mock_cred, \
         patch("orchestrator.AzureOpenAIChatClient") as mock_client, \
         patch("orchestrator.HandoffBuilder") as mock_builder:

        mock_settings.ai_foundry.use_foundry = False
        mock_settings.azure_openai.endpoint = "https://test.openai.azure.com"
        mock_settings.azure_openai.api_version = "2024-02-15"
        mock_settings.azure_openai.gpt_model = "gpt-4"
        mock_settings.azure_openai.gpt_model_mini = "gpt-4-mini"
        mock_settings.azure_openai.dalle_model = "dall-e-3"
        mock_settings.base_settings.azure_client_id = None

        mock_credential = MagicMock()
        mock_credential.get_token.return_value = MagicMock(token="test-token")
        mock_cred.return_value = mock_credential

        mock_chat_client = MagicMock()
        mock_chat_client.create_agent.return_value = MagicMock()
        mock_client.return_value = mock_chat_client

        mock_workflow = MagicMock()
        mock_builder_instance = MagicMock()
        mock_builder_instance.add_agent.return_value = mock_builder_instance
        mock_builder_instance.add_handoff.return_value = mock_builder_instance
        mock_builder_instance.build.return_value = mock_workflow
        mock_builder.return_value = mock_builder_instance

        orchestrator = ContentGenerationOrchestrator()
        orchestrator.initialize()

        # Mock RAI agent to pass
        mock_rai_agent = MagicMock()
        mock_rai_agent.run = AsyncMock(return_value="FALSE")
        orchestrator._rai_agent = mock_rai_agent

        # Mock planning agent with incomplete response
        incomplete_response = json.dumps({
            "status": "incomplete",
            "extracted_fields": {"overview": "Test campaign"},
            "missing_fields": ["target_audience", "deliverable"],
            "clarifying_message": "What is your target audience?"
        })
        mock_planning = MagicMock()
        mock_planning.run = AsyncMock(return_value=incomplete_response)
        orchestrator._agents["planning"] = mock_planning

        brief, clarifying, is_blocked = await orchestrator.parse_brief("Create a campaign")

        assert is_blocked is False
        assert clarifying == "What is your target audience?"


@pytest.mark.asyncio
async def test_parse_brief_json_in_code_block():
    """Test parse_brief extracts JSON from markdown code blocks."""
    with patch("orchestrator.app_settings") as mock_settings, \
         patch("orchestrator.DefaultAzureCredential") as mock_cred, \
         patch("orchestrator.AzureOpenAIChatClient") as mock_client, \
         patch("orchestrator.HandoffBuilder") as mock_builder:

        mock_settings.ai_foundry.use_foundry = False
        mock_settings.azure_openai.endpoint = "https://test.openai.azure.com"
        mock_settings.azure_openai.api_version = "2024-02-15"
        mock_settings.azure_openai.gpt_model = "gpt-4"
        mock_settings.azure_openai.gpt_model_mini = "gpt-4-mini"
        mock_settings.azure_openai.dalle_model = "dall-e-3"
        mock_settings.base_settings.azure_client_id = None

        mock_credential = MagicMock()
        mock_credential.get_token.return_value = MagicMock(token="test-token")
        mock_cred.return_value = mock_credential

        mock_chat_client = MagicMock()
        mock_chat_client.create_agent.return_value = MagicMock()
        mock_client.return_value = mock_chat_client

        mock_workflow = MagicMock()
        mock_builder_instance = MagicMock()
        mock_builder_instance.add_agent.return_value = mock_builder_instance
        mock_builder_instance.add_handoff.return_value = mock_builder_instance
        mock_builder_instance.build.return_value = mock_workflow
        mock_builder.return_value = mock_builder_instance

        orchestrator = ContentGenerationOrchestrator()
        orchestrator.initialize()

        mock_rai_agent = MagicMock()
        mock_rai_agent.run = AsyncMock(return_value="FALSE")
        orchestrator._rai_agent = mock_rai_agent

        # Response with JSON in code block
        code_block_response = '''Here is the analysis:
```json
{"status":"complete","extracted_fields":{"overview":"Test campaign","objectives":"Sell products","target_audience":"Adults","key_message":"Quality","tone_and_style":"Professional","deliverable":"Email","timelines":"","visual_guidelines":"","cta":""},"missing_fields":[],"clarifying_message":""}
```
'''
        mock_planning = MagicMock()
        mock_planning.run = AsyncMock(return_value=code_block_response)
        orchestrator._agents["planning"] = mock_planning

        brief, clarifying, is_blocked = await orchestrator.parse_brief("Create a campaign")

        assert is_blocked is False
        assert brief.overview == "Test campaign"


@pytest.mark.asyncio
async def test_generate_content_text_content():
    """Test generate_content produces text content."""
    with patch("orchestrator.app_settings") as mock_settings, \
         patch("orchestrator.DefaultAzureCredential") as mock_cred, \
         patch("orchestrator.AzureOpenAIChatClient") as mock_client, \
         patch("orchestrator.HandoffBuilder") as mock_builder:

        mock_settings.ai_foundry.use_foundry = False
        mock_settings.azure_openai.endpoint = "https://test.openai.azure.com"
        mock_settings.azure_openai.api_version = "2024-02-15"
        mock_settings.azure_openai.gpt_model = "gpt-4"
        mock_settings.azure_openai.gpt_model_mini = "gpt-4-mini"
        mock_settings.azure_openai.dalle_model = "dall-e-3"
        mock_settings.base_settings.azure_client_id = None

        mock_credential = MagicMock()
        mock_credential.get_token.return_value = MagicMock(token="test-token")
        mock_cred.return_value = mock_credential

        mock_chat_client = MagicMock()
        mock_chat_client.create_agent.return_value = MagicMock()
        mock_client.return_value = mock_chat_client

        mock_workflow = MagicMock()
        mock_builder_instance = MagicMock()
        mock_builder_instance.add_agent.return_value = mock_builder_instance
        mock_builder_instance.add_handoff.return_value = mock_builder_instance
        mock_builder_instance.build.return_value = mock_workflow
        mock_builder.return_value = mock_builder_instance

        from models import CreativeBrief

        orchestrator = ContentGenerationOrchestrator()
        orchestrator.initialize()

        # Mock agents
        mock_text_agent = MagicMock()
        mock_text_agent.run = AsyncMock(return_value="Generated marketing content")
        orchestrator._agents["text_content"] = mock_text_agent

        mock_compliance_agent = MagicMock()
        mock_compliance_agent.run = AsyncMock(return_value='{"issues":[],"overall_compliance":"pass"}')
        orchestrator._agents["compliance"] = mock_compliance_agent

        brief = CreativeBrief(
            overview="Test campaign",
            objectives="Sell products",
            target_audience="Adults",
            key_message="Quality",
            tone_and_style="Professional",
            deliverable="Email",
            timelines="",
            visual_guidelines="Modern style",
            cta=""
        )

        result = await orchestrator.generate_content(
            brief=brief,
            products=[{"product_name": "Paint", "description": "Blue paint"}],
            generate_images=False
        )

        assert "text_content" in result
        assert result["text_content"] == "Generated marketing content"


@pytest.mark.asyncio
async def test_regenerate_image_foundry_mode():
    """Test regenerate_image in Foundry mode."""
    with patch("orchestrator.app_settings") as mock_settings, \
         patch("orchestrator.DefaultAzureCredential") as mock_cred, \
         patch("orchestrator.AzureOpenAIChatClient") as mock_client, \
         patch("orchestrator.HandoffBuilder") as mock_builder:

        mock_settings.ai_foundry.use_foundry = True
        mock_settings.ai_foundry.image_endpoint = "https://image.openai.azure.com"
        mock_settings.ai_foundry.image_deployment = "dall-e-3"
        mock_settings.azure_openai.endpoint = "https://test.openai.azure.com"
        mock_settings.azure_openai.api_version = "2024-02-15"
        mock_settings.azure_openai.gpt_model = "gpt-4"
        mock_settings.azure_openai.gpt_model_mini = "gpt-4-mini"
        mock_settings.azure_openai.dalle_model = "dall-e-3"
        mock_settings.azure_openai.preview_api_version = "2024-02-01"
        mock_settings.base_settings.azure_client_id = None

        mock_credential = MagicMock()
        mock_credential.get_token.return_value = MagicMock(token="test-token")
        mock_cred.return_value = mock_credential

        mock_chat_client = MagicMock()
        mock_chat_client.create_agent.return_value = MagicMock()
        mock_client.return_value = mock_chat_client

        mock_workflow = MagicMock()
        mock_builder_instance = MagicMock()
        mock_builder_instance.add_agent.return_value = mock_builder_instance
        mock_builder_instance.add_handoff.return_value = mock_builder_instance
        mock_builder_instance.build.return_value = mock_workflow
        mock_builder.return_value = mock_builder_instance

        from models import CreativeBrief

        orchestrator = ContentGenerationOrchestrator()
        orchestrator.initialize()

        brief = CreativeBrief(
            overview="Test", objectives="Sell", target_audience="Adults",
            key_message="Quality", tone_and_style="Pro", deliverable="Email",
            timelines="", visual_guidelines="Modern", cta=""
        )

        with patch.object(orchestrator, '_generate_foundry_image', new=AsyncMock()):
            result = await orchestrator.regenerate_image(
                modification_request="Make it more colorful",
                brief=brief,
                products=[{"product_name": "Paint", "description": "Blue"}],
                previous_image_prompt="previous prompt"
            )

        assert "image_prompt" in result
        assert "message" in result


@pytest.mark.asyncio
async def test_regenerate_image_exception():
    """Test regenerate_image handles exceptions gracefully."""
    with patch("orchestrator.app_settings") as mock_settings, \
         patch("orchestrator.DefaultAzureCredential") as mock_cred, \
         patch("orchestrator.AzureOpenAIChatClient") as mock_client, \
         patch("orchestrator.HandoffBuilder") as mock_builder:

        mock_settings.ai_foundry.use_foundry = True
        mock_settings.ai_foundry.image_endpoint = "https://image.openai.azure.com"
        mock_settings.ai_foundry.image_deployment = "dall-e-3"
        mock_settings.azure_openai.endpoint = "https://test.openai.azure.com"
        mock_settings.azure_openai.api_version = "2024-02-15"
        mock_settings.azure_openai.gpt_model = "gpt-4"
        mock_settings.azure_openai.gpt_model_mini = "gpt-4-mini"
        mock_settings.azure_openai.dalle_model = "dall-e-3"
        mock_settings.azure_openai.preview_api_version = "2024-02-01"
        mock_settings.base_settings.azure_client_id = None

        mock_credential = MagicMock()
        mock_credential.get_token.return_value = MagicMock(token="test-token")
        mock_cred.return_value = mock_credential

        mock_chat_client = MagicMock()
        mock_chat_client.create_agent.return_value = MagicMock()
        mock_client.return_value = mock_chat_client

        mock_workflow = MagicMock()
        mock_builder_instance = MagicMock()
        mock_builder_instance.add_agent.return_value = mock_builder_instance
        mock_builder_instance.add_handoff.return_value = mock_builder_instance
        mock_builder_instance.build.return_value = mock_workflow
        mock_builder.return_value = mock_builder_instance

        from models import CreativeBrief

        orchestrator = ContentGenerationOrchestrator()
        orchestrator.initialize()

        brief = CreativeBrief(
            overview="Test", objectives="Sell", target_audience="Adults",
            key_message="Quality", tone_and_style="Pro", deliverable="Email",
            timelines="", visual_guidelines="Modern", cta=""
        )

        with patch.object(orchestrator, '_generate_foundry_image', new=AsyncMock(side_effect=Exception("Test error"))):
            result = await orchestrator.regenerate_image(
                modification_request="Change",
                brief=brief,
                products=[],
                previous_image_prompt=None
            )

        assert "error" in result


@pytest.mark.asyncio
async def test_generate_foundry_image_credential_none_returns_error():
    """Test _generate_foundry_image when credential is None returns error."""
    with patch("orchestrator.app_settings") as mock_settings, \
         patch("orchestrator.DefaultAzureCredential") as mock_cred:

        mock_settings.ai_foundry.use_foundry = True
        mock_settings.ai_foundry.image_endpoint = "https://image.openai.azure.com"
        mock_settings.ai_foundry.image_deployment = "dall-e-3"
        mock_settings.azure_openai.endpoint = "https://test.openai.azure.com"
        mock_settings.azure_openai.image_model = "dall-e-3"
        mock_settings.azure_openai.preview_api_version = "2024-02-01"
        mock_settings.base_settings.azure_client_id = None

        mock_cred.return_value = None

        orchestrator = ContentGenerationOrchestrator()
        orchestrator._credential = None

        results = {}
        await orchestrator._generate_foundry_image("Test prompt", results)

        assert "image_error" in results


@pytest.mark.asyncio
async def test_generate_foundry_image_no_image_endpoint():
    """Test _generate_foundry_image with no endpoint."""
    with patch("orchestrator.app_settings") as mock_settings, \
         patch("orchestrator.DefaultAzureCredential") as mock_cred:

        mock_settings.ai_foundry.use_foundry = True
        mock_settings.ai_foundry.image_endpoint = None
        mock_settings.ai_foundry.image_deployment = None
        mock_settings.azure_openai.endpoint = None
        mock_settings.azure_openai.image_model = None
        mock_settings.base_settings.azure_client_id = None

        mock_credential = MagicMock()
        mock_credential.get_token.return_value = MagicMock(token="test-token")
        mock_cred.return_value = mock_credential

        orchestrator = ContentGenerationOrchestrator()
        orchestrator._credential = mock_credential

        results = {}
        await orchestrator._generate_foundry_image("Test prompt", results)

        assert "image_error" in results


@pytest.mark.asyncio
async def test_get_chat_client_foundry_mode():
    """Test _get_chat_client in Foundry mode."""
    with patch("orchestrator.app_settings") as mock_settings, \
         patch("orchestrator.DefaultAzureCredential") as mock_cred, \
         patch("orchestrator.AzureOpenAIChatClient") as mock_client, \
         patch("orchestrator.FOUNDRY_AVAILABLE", True):

        mock_settings.ai_foundry.use_foundry = True
        mock_settings.ai_foundry.model_deployment = "gpt-4-foundry"
        mock_settings.azure_openai.endpoint = "https://test.openai.azure.com"
        mock_settings.azure_openai.api_version = "2024-02-15"
        mock_settings.azure_openai.gpt_model = "gpt-4"
        mock_settings.base_settings.azure_client_id = None

        mock_credential = MagicMock()
        mock_credential.get_token.return_value = MagicMock(token="test-token")
        mock_cred.return_value = mock_credential

        mock_chat_instance = MagicMock()
        mock_client.return_value = mock_chat_instance

        orchestrator = ContentGenerationOrchestrator()
        orchestrator._use_foundry = True

        client = orchestrator._get_chat_client()

        assert client == mock_chat_instance
        mock_client.assert_called_once()


def test_foundry_not_available():
    """Test when Foundry SDK is not available."""
    # Check that FOUNDRY_AVAILABLE is defined
    assert hasattr(orch_module, 'FOUNDRY_AVAILABLE')

# Tests for workflow event handling (lines 736-799, 841-895)
# Note: These are integration-level tests that verify the workflow event
# handling code paths. Due to isinstance checks in the code, we use
# actual event types where possible.


@pytest.mark.asyncio
async def test_process_message_with_context():
    """Test process_message with context parameter."""
    with patch("orchestrator.app_settings") as mock_settings, \
         patch("orchestrator.DefaultAzureCredential") as mock_cred, \
         patch("orchestrator.AzureOpenAIChatClient") as mock_client:

        mock_settings.ai_foundry.use_foundry = False
        mock_settings.azure_openai.endpoint = "https://test.openai.azure.com"
        mock_settings.azure_openai.api_version = "2024-02-15"
        mock_settings.azure_openai.gpt_model = "gpt-4"
        mock_settings.azure_openai.gpt_model_mini = "gpt-4-mini"
        mock_settings.azure_openai.dalle_model = "dall-e-3"
        mock_settings.base_settings.azure_client_id = None

        mock_credential = MagicMock()
        mock_credential.get_token.return_value = MagicMock(token="test-token")
        mock_cred.return_value = mock_credential

        mock_chat_client = MagicMock()
        mock_chat_client.create_agent.return_value = MagicMock()
        mock_client.return_value = mock_chat_client

        # Track if workflow was called
        call_tracker = {"called": False, "input": None}

        async def mock_stream(input_text):
            call_tracker["called"] = True
            call_tracker["input"] = input_text
            if False:
                yield  # Make it an async generator

        mock_workflow = MagicMock()
        mock_workflow.run_stream = mock_stream

        orchestrator = ContentGenerationOrchestrator()
        orchestrator._initialized = True  # Mark as initialized
        orchestrator._workflow = mock_workflow  # Inject our mock workflow directly

        # Test with context parameter (exercises line 731-732)
        context = {"previous_messages": ["Hello"], "user_preference": "blue"}
        responses = []
        async for response in orchestrator.process_message(
            "Create content",
            conversation_id="conv-123",
            context=context
        ):
            responses.append(response)

        # Workflow was called with context embedded in input
        assert call_tracker["called"] is True
        assert "Context:" in call_tracker["input"]
        assert "user_preference" in call_tracker["input"]


@pytest.mark.asyncio
async def test_send_user_response_safe_content():
    """Test send_user_response allows safe content through."""
    with patch("orchestrator.app_settings") as mock_settings, \
         patch("orchestrator.DefaultAzureCredential") as mock_cred, \
         patch("orchestrator.AzureOpenAIChatClient") as mock_client:

        mock_settings.ai_foundry.use_foundry = False
        mock_settings.azure_openai.endpoint = "https://test.openai.azure.com"
        mock_settings.azure_openai.api_version = "2024-02-15"
        mock_settings.azure_openai.gpt_model = "gpt-4"
        mock_settings.azure_openai.gpt_model_mini = "gpt-4-mini"
        mock_settings.azure_openai.dalle_model = "dall-e-3"
        mock_settings.base_settings.azure_client_id = None

        mock_credential = MagicMock()
        mock_credential.get_token.return_value = MagicMock(token="test-token")
        mock_cred.return_value = mock_credential

        mock_chat_client = MagicMock()
        mock_chat_client.create_agent.return_value = MagicMock()
        mock_client.return_value = mock_chat_client

        call_tracker = {"called": False, "responses": None}

        async def mock_send(responses):
            call_tracker["called"] = True
            call_tracker["responses"] = responses
            if False:
                yield  # async generator

        mock_workflow = MagicMock()
        mock_workflow.send_responses_streaming = mock_send

        orchestrator = ContentGenerationOrchestrator()
        orchestrator._initialized = True  # Mark as initialized
        orchestrator._workflow = mock_workflow  # Inject our mock workflow directly

        # Test safe content passes through (exercises line 841-843 RAI check)
        responses = []
        async for response in orchestrator.send_user_response(
            request_id="req-123",
            user_response="I choose product A and want blue color",
            conversation_id="conv-123"
        ):
            responses.append(response)

        # Workflow was called (not blocked by RAI)
        assert call_tracker["called"] is True


@pytest.mark.asyncio
async def test_parse_brief_json_with_backticks():
    """Test parse_brief extracting JSON from ```json blocks."""
    with patch("orchestrator.app_settings") as mock_settings, \
         patch("orchestrator.DefaultAzureCredential") as mock_cred, \
         patch("orchestrator.AzureOpenAIChatClient") as mock_client, \
         patch("orchestrator.HandoffBuilder") as mock_builder:

        mock_settings.ai_foundry.use_foundry = False
        mock_settings.azure_openai.endpoint = "https://test.openai.azure.com"
        mock_settings.azure_openai.api_version = "2024-02-15"
        mock_settings.azure_openai.gpt_model = "gpt-4"
        mock_settings.azure_openai.gpt_model_mini = "gpt-4-mini"
        mock_settings.azure_openai.dalle_model = "dall-e-3"
        mock_settings.base_settings.azure_client_id = None

        mock_credential = MagicMock()
        mock_credential.get_token.return_value = MagicMock(token="test-token")
        mock_cred.return_value = mock_credential

        mock_chat_client = MagicMock()
        mock_chat_client.create_agent.return_value = MagicMock()
        mock_client.return_value = mock_chat_client

        # Mock planning agent to return JSON in ```json block
        mock_planning_agent = AsyncMock()
        mock_planning_agent.run.return_value = '''Here's the analysis:
```json
{
    "status": "complete",
    "extracted_fields": {
        "overview": "Summer paint campaign",
        "objectives": "Increase sales by 20%",
        "target_audience": "Homeowners 30-50",
        "key_message": "Beautiful lasting colors",
        "tone_and_style": "Professional, warm",
        "deliverable": "Social media post",
        "timelines": "Q2 2024",
        "visual_guidelines": "Bright, modern",
        "cta": "Shop Now"
    },
    "missing_fields": [],
    "clarifying_message": ""
}
```'''

        mock_rai_agent = AsyncMock()
        mock_rai_agent.run.return_value = "FALSE"

        mock_workflow = MagicMock()
        mock_builder_instance = MagicMock()
        mock_builder_instance.add_agent.return_value = mock_builder_instance
        mock_builder_instance.add_handoff.return_value = mock_builder_instance
        mock_builder_instance.build.return_value = mock_workflow
        mock_builder.return_value = mock_builder_instance

        orchestrator = ContentGenerationOrchestrator()
        orchestrator.initialize()
        orchestrator._agents["planning"] = mock_planning_agent
        orchestrator._rai_agent = mock_rai_agent

        brief, clarifying, is_blocked = await orchestrator.parse_brief("Create a summer paint campaign targeting homeowners")

        assert is_blocked is False
        assert brief.objectives == "Increase sales by 20%"
        assert brief.target_audience == "Homeowners 30-50"


@pytest.mark.asyncio
async def test_parse_brief_with_dict_field_value():
    """Test parse_brief handles dict values in extracted_fields."""
    with patch("orchestrator.app_settings") as mock_settings, \
         patch("orchestrator.DefaultAzureCredential") as mock_cred, \
         patch("orchestrator.AzureOpenAIChatClient") as mock_client, \
         patch("orchestrator.HandoffBuilder") as mock_builder:

        mock_settings.ai_foundry.use_foundry = False
        mock_settings.azure_openai.endpoint = "https://test.openai.azure.com"
        mock_settings.azure_openai.api_version = "2024-02-15"
        mock_settings.azure_openai.gpt_model = "gpt-4"
        mock_settings.azure_openai.gpt_model_mini = "gpt-4-mini"
        mock_settings.azure_openai.dalle_model = "dall-e-3"
        mock_settings.base_settings.azure_client_id = None

        mock_credential = MagicMock()
        mock_credential.get_token.return_value = MagicMock(token="test-token")
        mock_cred.return_value = mock_credential

        mock_chat_client = MagicMock()
        mock_chat_client.create_agent.return_value = MagicMock()
        mock_client.return_value = mock_chat_client

        # Mock planning agent with dict field values (line 1031)
        mock_planning_agent = AsyncMock()
        response_json = {
            "status": "complete",
            "extracted_fields": {
                "overview": "Campaign overview",
                "objectives": {"primary": "sales", "secondary": "awareness"},  # dict value
                "target_audience": ["homeowners", "designers"],  # list value
                "key_message": None,  # None value
                "tone_and_style": 123,  # non-string value
                "deliverable": "Email",
                "timelines": "Q1",
                "visual_guidelines": "Modern",
                "cta": "Buy"
            },
            "missing_fields": [],
            "clarifying_message": ""
        }
        mock_planning_agent.run.return_value = json.dumps(response_json)

        mock_rai_agent = AsyncMock()
        mock_rai_agent.run.return_value = "FALSE"

        mock_workflow = MagicMock()
        mock_builder_instance = MagicMock()
        mock_builder_instance.add_agent.return_value = mock_builder_instance
        mock_builder_instance.add_handoff.return_value = mock_builder_instance
        mock_builder_instance.build.return_value = mock_workflow
        mock_builder.return_value = mock_builder_instance

        orchestrator = ContentGenerationOrchestrator()
        orchestrator.initialize()
        orchestrator._agents["planning"] = mock_planning_agent
        orchestrator._rai_agent = mock_rai_agent

        brief, clarifying, is_blocked = await orchestrator.parse_brief("Create campaign")

        assert is_blocked is False
        # Dict should be converted to string
        assert "primary" in brief.objectives
        # List should be converted to comma-separated
        assert "homeowners" in brief.target_audience
        # None should be empty string
        assert brief.key_message == ""
        # Number should be converted to string
        assert brief.tone_and_style == "123"


@pytest.mark.asyncio
async def test_parse_brief_fallback_extraction():
    """Test parse_brief falls back to _extract_brief_from_text on parse error."""
    with patch("orchestrator.app_settings") as mock_settings, \
         patch("orchestrator.DefaultAzureCredential") as mock_cred, \
         patch("orchestrator.AzureOpenAIChatClient") as mock_client, \
         patch("orchestrator.HandoffBuilder") as mock_builder:

        mock_settings.ai_foundry.use_foundry = False
        mock_settings.azure_openai.endpoint = "https://test.openai.azure.com"
        mock_settings.azure_openai.api_version = "2024-02-15"
        mock_settings.azure_openai.gpt_model = "gpt-4"
        mock_settings.azure_openai.gpt_model_mini = "gpt-4-mini"
        mock_settings.azure_openai.dalle_model = "dall-e-3"
        mock_settings.base_settings.azure_client_id = None

        mock_credential = MagicMock()
        mock_credential.get_token.return_value = MagicMock(token="test-token")
        mock_cred.return_value = mock_credential

        mock_chat_client = MagicMock()
        mock_chat_client.create_agent.return_value = MagicMock()
        mock_client.return_value = mock_chat_client

        # Mock planning agent with invalid JSON
        mock_planning_agent = AsyncMock()
        mock_planning_agent.run.return_value = "This is not valid JSON at all"

        mock_rai_agent = AsyncMock()
        mock_rai_agent.run.return_value = "FALSE"

        mock_workflow = MagicMock()
        mock_builder_instance = MagicMock()
        mock_builder_instance.add_agent.return_value = mock_builder_instance
        mock_builder_instance.add_handoff.return_value = mock_builder_instance
        mock_builder_instance.build.return_value = mock_workflow
        mock_builder.return_value = mock_builder_instance

        orchestrator = ContentGenerationOrchestrator()
        orchestrator.initialize()
        orchestrator._agents["planning"] = mock_planning_agent
        orchestrator._rai_agent = mock_rai_agent

        brief, clarifying, is_blocked = await orchestrator.parse_brief(
            "Overview: Test campaign\nObjectives: Increase sales"
        )

        # Should not be blocked, should use fallback extraction
        assert is_blocked is False
        assert brief is not None


@pytest.mark.asyncio
async def test_generate_foundry_image_success():
    """Test successful Foundry image generation via HTTP."""
    with patch("orchestrator.app_settings") as mock_settings, \
         patch("orchestrator.DefaultAzureCredential") as mock_cred, \
         patch("httpx.AsyncClient") as mock_httpx:

        mock_settings.ai_foundry.use_foundry = True
        mock_settings.ai_foundry.image_deployment = "gpt-image-1-mini"
        mock_settings.azure_openai.endpoint = "https://test.openai.azure.com"
        mock_settings.azure_openai.image_model = "gpt-image-1-mini"
        mock_settings.azure_openai.image_api_version = "2025-04-01-preview"
        mock_settings.azure_openai.image_size = "1024x1024"
        mock_settings.azure_openai.image_quality = "medium"
        mock_settings.azure_openai.preview_api_version = "2024-02-01"
        mock_settings.base_settings.azure_client_id = None

        mock_credential = MagicMock()
        mock_credential.get_token.return_value = MagicMock(token="test-token")
        mock_cred.return_value = mock_credential

        # Mock successful HTTP response
        test_image_data = base64.b64encode(b"fake_image_bytes").decode()

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [{"b64_json": test_image_data, "revised_prompt": "A beautiful image"}]
        }

        mock_client_instance = MagicMock()
        mock_client_instance.post = AsyncMock(return_value=mock_response)
        mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_client_instance.__aexit__ = AsyncMock(return_value=None)
        mock_httpx.return_value = mock_client_instance

        orchestrator = ContentGenerationOrchestrator()
        orchestrator._credential = mock_credential

        # Mock _save_image_to_blob
        orchestrator._save_image_to_blob = AsyncMock()

        results = {}
        await orchestrator._generate_foundry_image("Create a product image", results)

        # Should have called save_image_to_blob
        orchestrator._save_image_to_blob.assert_called_once()
        assert "image_revised_prompt" in results or "image_error" not in results


@pytest.mark.asyncio
async def test_generate_foundry_image_dalle3_mode():
    """Test Foundry image generation with DALL-E 3 model."""
    with patch("orchestrator.app_settings") as mock_settings, \
         patch("orchestrator.DefaultAzureCredential") as mock_cred, \
         patch("httpx.AsyncClient") as mock_httpx:

        mock_settings.ai_foundry.use_foundry = True
        mock_settings.ai_foundry.image_deployment = "dall-e-3"  # DALL-E model
        mock_settings.azure_openai.endpoint = "https://test.openai.azure.com"
        mock_settings.azure_openai.image_model = "dall-e-3"
        mock_settings.azure_openai.preview_api_version = "2024-02-01"
        mock_settings.azure_openai.image_api_version = "2025-04-01-preview"
        mock_settings.azure_openai.image_size = "1024x1024"
        mock_settings.azure_openai.image_quality = "hd"
        mock_settings.base_settings.azure_client_id = None

        mock_credential = MagicMock()
        mock_credential.get_token.return_value = MagicMock(token="test-token")
        mock_cred.return_value = mock_credential

        test_image_data = base64.b64encode(b"dalle3_image").decode()

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [{"b64_json": test_image_data}]
        }

        mock_client_instance = MagicMock()
        mock_client_instance.post = AsyncMock(return_value=mock_response)
        mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_client_instance.__aexit__ = AsyncMock(return_value=None)
        mock_httpx.return_value = mock_client_instance

        orchestrator = ContentGenerationOrchestrator()
        orchestrator._credential = mock_credential
        orchestrator._save_image_to_blob = AsyncMock()

        results = {}
        await orchestrator._generate_foundry_image("A" * 5000, results)  # Long prompt

        # DALL-E 3 should truncate prompt to 4000 chars
        call_args = mock_client_instance.post.call_args
        if call_args:
            payload = call_args.kwargs.get("json", {})
            prompt_len = len(payload.get("prompt", ""))
            assert prompt_len <= 4000


@pytest.mark.asyncio
async def test_generate_foundry_image_api_error():
    """Test Foundry image generation handles API errors."""
    with patch("orchestrator.app_settings") as mock_settings, \
         patch("orchestrator.DefaultAzureCredential") as mock_cred, \
         patch("httpx.AsyncClient") as mock_httpx:

        mock_settings.ai_foundry.use_foundry = True
        mock_settings.ai_foundry.image_deployment = "gpt-image-1-mini"
        mock_settings.azure_openai.endpoint = "https://test.openai.azure.com"
        mock_settings.azure_openai.image_model = "gpt-image-1-mini"
        mock_settings.azure_openai.image_api_version = "2025-04-01-preview"
        mock_settings.azure_openai.image_size = "1024x1024"
        mock_settings.azure_openai.image_quality = "medium"
        mock_settings.base_settings.azure_client_id = None

        mock_credential = MagicMock()
        mock_credential.get_token.return_value = MagicMock(token="test-token")
        mock_cred.return_value = mock_credential

        # Mock error HTTP response
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"

        mock_client_instance = MagicMock()
        mock_client_instance.post = AsyncMock(return_value=mock_response)
        mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_client_instance.__aexit__ = AsyncMock(return_value=None)
        mock_httpx.return_value = mock_client_instance

        orchestrator = ContentGenerationOrchestrator()
        orchestrator._credential = mock_credential

        results = {}
        await orchestrator._generate_foundry_image("Create image", results)

        assert "image_error" in results
        assert "500" in results["image_error"]


@pytest.mark.asyncio
async def test_generate_foundry_image_timeout():
    """Test Foundry image generation handles timeout."""
    with patch("orchestrator.app_settings") as mock_settings, \
         patch("orchestrator.DefaultAzureCredential") as mock_cred, \
         patch("httpx.AsyncClient") as mock_httpx:

        mock_settings.ai_foundry.use_foundry = True
        mock_settings.ai_foundry.image_deployment = "gpt-image-1-mini"
        mock_settings.azure_openai.endpoint = "https://test.openai.azure.com"
        mock_settings.azure_openai.image_model = "gpt-image-1-mini"
        mock_settings.azure_openai.image_api_version = "2025-04-01-preview"
        mock_settings.azure_openai.image_size = "1024x1024"
        mock_settings.azure_openai.image_quality = "medium"
        mock_settings.base_settings.azure_client_id = None

        mock_credential = MagicMock()
        mock_credential.get_token.return_value = MagicMock(token="test-token")
        mock_cred.return_value = mock_credential

        import httpx

        mock_client_instance = MagicMock()
        mock_client_instance.post = AsyncMock(side_effect=httpx.TimeoutException("Timeout"))
        mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_client_instance.__aexit__ = AsyncMock(return_value=None)
        mock_httpx.return_value = mock_client_instance

        orchestrator = ContentGenerationOrchestrator()
        orchestrator._credential = mock_credential

        results = {}
        await orchestrator._generate_foundry_image("Create image", results)

        assert "image_error" in results
        assert "timed out" in results["image_error"].lower()


@pytest.mark.asyncio
async def test_generate_foundry_image_url_fallback():
    """Test Foundry image fetches from URL when b64 not provided."""
    with patch("orchestrator.app_settings") as mock_settings, \
         patch("orchestrator.DefaultAzureCredential") as mock_cred, \
         patch("httpx.AsyncClient") as mock_httpx:

        mock_settings.ai_foundry.use_foundry = True
        mock_settings.ai_foundry.image_deployment = "gpt-image-1-mini"
        mock_settings.azure_openai.endpoint = "https://test.openai.azure.com"
        mock_settings.azure_openai.image_model = "gpt-image-1-mini"
        mock_settings.azure_openai.image_api_version = "2025-04-01-preview"
        mock_settings.azure_openai.image_size = "1024x1024"
        mock_settings.azure_openai.image_quality = "medium"
        mock_settings.base_settings.azure_client_id = None

        mock_credential = MagicMock()
        mock_credential.get_token.return_value = MagicMock(token="test-token")
        mock_cred.return_value = mock_credential

        # Response with URL instead of b64
        mock_post_response = MagicMock()
        mock_post_response.status_code = 200
        mock_post_response.json.return_value = {
            "data": [{"url": "https://example.com/image.png"}]
        }

        # Mock GET response for fetching image from URL
        mock_get_response = MagicMock()
        mock_get_response.status_code = 200
        mock_get_response.content = b"image_bytes_from_url"

        mock_client_instance = MagicMock()
        mock_client_instance.post = AsyncMock(return_value=mock_post_response)
        mock_client_instance.get = AsyncMock(return_value=mock_get_response)
        mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_client_instance.__aexit__ = AsyncMock(return_value=None)
        mock_httpx.return_value = mock_client_instance

        orchestrator = ContentGenerationOrchestrator()
        orchestrator._credential = mock_credential
        orchestrator._save_image_to_blob = AsyncMock()

        results = {}
        await orchestrator._generate_foundry_image("Create image", results)

        # Should have fetched from URL
        mock_client_instance.get.assert_called_once()
        orchestrator._save_image_to_blob.assert_called_once()


@pytest.mark.asyncio
async def test_generate_content_with_foundry_image():
    """Test generate_content generates images in Foundry mode."""
    with patch("orchestrator.app_settings") as mock_settings, \
         patch("orchestrator.DefaultAzureCredential") as mock_cred, \
         patch("orchestrator.AzureOpenAIChatClient") as mock_client, \
         patch("orchestrator.HandoffBuilder") as mock_builder:

        mock_settings.ai_foundry.use_foundry = True
        mock_settings.ai_foundry.model_deployment = "gpt-4"
        mock_settings.azure_openai.endpoint = "https://test.openai.azure.com"
        mock_settings.azure_openai.api_version = "2024-02-15"
        mock_settings.azure_openai.gpt_model = "gpt-4"
        mock_settings.azure_openai.gpt_model_mini = "gpt-4-mini"
        mock_settings.azure_openai.dalle_model = "dall-e-3"
        mock_settings.base_settings.azure_client_id = None

        mock_credential = MagicMock()
        mock_credential.get_token.return_value = MagicMock(token="test-token")
        mock_cred.return_value = mock_credential

        mock_chat_client = MagicMock()
        mock_chat_client.create_agent.return_value = MagicMock()
        mock_client.return_value = mock_chat_client

        # Mock agents
        mock_text_agent = AsyncMock()
        mock_text_agent.run.return_value = "Great marketing headline here!"

        mock_compliance_agent = AsyncMock()
        mock_compliance_agent.run.return_value = json.dumps({"violations": []})

        mock_workflow = MagicMock()
        mock_builder_instance = MagicMock()
        mock_builder_instance.add_agent.return_value = mock_builder_instance
        mock_builder_instance.add_handoff.return_value = mock_builder_instance
        mock_builder_instance.build.return_value = mock_workflow
        mock_builder.return_value = mock_builder_instance

        from models import CreativeBrief

        orchestrator = ContentGenerationOrchestrator()
        orchestrator.initialize()
        orchestrator._use_foundry = True
        orchestrator._agents["text_content"] = mock_text_agent
        orchestrator._agents["compliance"] = mock_compliance_agent
        orchestrator._generate_foundry_image = AsyncMock()

        brief = CreativeBrief(
            overview="Test campaign",
            objectives="Increase sales",
            target_audience="Adults 25-45",
            key_message="Quality products",
            tone_and_style="Professional",
            deliverable="Social post",
            timelines="Q1",
            visual_guidelines="Modern, clean",
            cta="Shop Now"
        )

        result = await orchestrator.generate_content(
            brief=brief,
            products=[{"product_name": "Test Paint", "description": "Blue paint"}],
            generate_images=True
        )

        assert result["text_content"] == "Great marketing headline here!"
        # In Foundry mode, should call _generate_foundry_image
        orchestrator._generate_foundry_image.assert_called_once()


@pytest.mark.asyncio
async def test_generate_content_direct_mode_image():
    """Test generate_content generates images in Direct mode."""
    with patch("orchestrator.app_settings") as mock_settings, \
         patch("orchestrator.DefaultAzureCredential") as mock_cred, \
         patch("orchestrator.AzureOpenAIChatClient") as mock_client, \
         patch("orchestrator.HandoffBuilder") as mock_builder, \
         patch("agents.image_content_agent.generate_image") as mock_generate_image:

        mock_settings.ai_foundry.use_foundry = False
        mock_settings.azure_openai.endpoint = "https://test.openai.azure.com"
        mock_settings.azure_openai.api_version = "2024-02-15"
        mock_settings.azure_openai.gpt_model = "gpt-4"
        mock_settings.azure_openai.gpt_model_mini = "gpt-4-mini"
        mock_settings.azure_openai.dalle_model = "dall-e-3"
        mock_settings.base_settings.azure_client_id = None

        mock_credential = MagicMock()
        mock_credential.get_token.return_value = MagicMock(token="test-token")
        mock_cred.return_value = mock_credential

        mock_chat_client = MagicMock()
        mock_chat_client.create_agent.return_value = MagicMock()
        mock_client.return_value = mock_chat_client

        mock_text_agent = AsyncMock()
        mock_text_agent.run.return_value = "Marketing content"

        mock_image_agent = AsyncMock()
        mock_image_agent.run.return_value = json.dumps({"prompt": "A beautiful product image"})

        mock_compliance_agent = AsyncMock()
        mock_compliance_agent.run.return_value = json.dumps({"violations": []})

        # Mock generate_image function
        mock_generate_image.return_value = {
            "success": True,
            "image_base64": base64.b64encode(b"fake_image").decode(),
            "revised_prompt": "Enhanced prompt"
        }

        mock_workflow = MagicMock()
        mock_builder_instance = MagicMock()
        mock_builder_instance.add_agent.return_value = mock_builder_instance
        mock_builder_instance.add_handoff.return_value = mock_builder_instance
        mock_builder_instance.build.return_value = mock_workflow
        mock_builder.return_value = mock_builder_instance

        from models import CreativeBrief

        orchestrator = ContentGenerationOrchestrator()
        orchestrator.initialize()
        orchestrator._use_foundry = False
        orchestrator._agents["text_content"] = mock_text_agent
        orchestrator._agents["image_content"] = mock_image_agent
        orchestrator._agents["compliance"] = mock_compliance_agent
        orchestrator._save_image_to_blob = AsyncMock()

        brief = CreativeBrief(
            overview="Test",
            objectives="Test",
            target_audience="Test",
            key_message="Test",
            tone_and_style="Test",
            deliverable="Test",
            timelines="Test",
            visual_guidelines="Modern",
            cta="Test"
        )

        result = await orchestrator.generate_content(
            brief=brief,
            products=[],
            generate_images=True
        )

        assert "text_content" in result
        mock_generate_image.assert_called_once()


@pytest.mark.asyncio
async def test_regenerate_image_direct_mode():
    """Test regenerate_image in Direct mode."""
    with patch("orchestrator.app_settings") as mock_settings, \
         patch("orchestrator.DefaultAzureCredential") as mock_cred, \
         patch("orchestrator.AzureOpenAIChatClient") as mock_client, \
         patch("orchestrator.HandoffBuilder") as mock_builder, \
         patch("agents.image_content_agent.generate_image") as mock_generate_image:

        mock_settings.ai_foundry.use_foundry = False
        mock_settings.azure_openai.endpoint = "https://test.openai.azure.com"
        mock_settings.azure_openai.api_version = "2024-02-15"
        mock_settings.azure_openai.gpt_model = "gpt-4"
        mock_settings.azure_openai.gpt_model_mini = "gpt-4-mini"
        mock_settings.azure_openai.dalle_model = "dall-e-3"
        mock_settings.base_settings.azure_client_id = None

        mock_credential = MagicMock()
        mock_credential.get_token.return_value = MagicMock(token="test-token")
        mock_cred.return_value = mock_credential

        mock_chat_client = MagicMock()
        mock_chat_client.create_agent.return_value = MagicMock()
        mock_client.return_value = mock_chat_client

        mock_image_agent = AsyncMock()
        mock_image_agent.run.return_value = json.dumps({
            "prompt": "Modified product image prompt",
            "change_summary": "Added more vibrant colors"
        })

        mock_generate_image.return_value = {
            "success": True,
            "image_base64": base64.b64encode(b"regenerated_image").decode(),
            "revised_prompt": "Enhanced modified prompt"
        }

        mock_workflow = MagicMock()
        mock_builder_instance = MagicMock()
        mock_builder_instance.add_agent.return_value = mock_builder_instance
        mock_builder_instance.add_handoff.return_value = mock_builder_instance
        mock_builder_instance.build.return_value = mock_workflow
        mock_builder.return_value = mock_builder_instance

        from models import CreativeBrief

        orchestrator = ContentGenerationOrchestrator()
        orchestrator.initialize()
        orchestrator._use_foundry = False
        orchestrator._agents["image_content"] = mock_image_agent
        orchestrator._save_image_to_blob = AsyncMock()

        brief = CreativeBrief(
            overview="Test",
            objectives="Test",
            target_audience="Test",
            key_message="Test",
            tone_and_style="Test",
            deliverable="Test",
            timelines="Test",
            visual_guidelines="Vibrant colors",
            cta="Test"
        )

        result = await orchestrator.regenerate_image(
            brief=brief,
            previous_image_prompt="Original product image",
            modification_request="Make colors more vibrant",
            products=[]
        )

        assert "image_prompt" in result
        mock_generate_image.assert_called_once()


@pytest.mark.asyncio
async def test_regenerate_image_failure():
    """Test regenerate_image handles generation failure."""
    with patch("orchestrator.app_settings") as mock_settings, \
         patch("orchestrator.DefaultAzureCredential") as mock_cred, \
         patch("orchestrator.AzureOpenAIChatClient") as mock_client, \
         patch("orchestrator.HandoffBuilder") as mock_builder, \
         patch("agents.image_content_agent.generate_image") as mock_generate_image:

        mock_settings.ai_foundry.use_foundry = False
        mock_settings.azure_openai.endpoint = "https://test.openai.azure.com"
        mock_settings.azure_openai.api_version = "2024-02-15"
        mock_settings.azure_openai.gpt_model = "gpt-4"
        mock_settings.azure_openai.gpt_model_mini = "gpt-4-mini"
        mock_settings.azure_openai.dalle_model = "dall-e-3"
        mock_settings.base_settings.azure_client_id = None

        mock_credential = MagicMock()
        mock_credential.get_token.return_value = MagicMock(token="test-token")
        mock_cred.return_value = mock_credential

        mock_chat_client = MagicMock()
        mock_chat_client.create_agent.return_value = MagicMock()
        mock_client.return_value = mock_chat_client

        mock_image_agent = AsyncMock()
        mock_image_agent.run.return_value = "Modified prompt"

        # Mock generate_image failure
        mock_generate_image.return_value = {
            "success": False,
            "error": "Content policy violation"
        }

        mock_workflow = MagicMock()
        mock_builder_instance = MagicMock()
        mock_builder_instance.add_agent.return_value = mock_builder_instance
        mock_builder_instance.add_handoff.return_value = mock_builder_instance
        mock_builder_instance.build.return_value = mock_workflow
        mock_builder.return_value = mock_builder_instance

        from models import CreativeBrief

        orchestrator = ContentGenerationOrchestrator()
        orchestrator.initialize()
        orchestrator._use_foundry = False
        orchestrator._agents["image_content"] = mock_image_agent

        brief = CreativeBrief(
            overview="Test", objectives="Test", target_audience="Test",
            key_message="Test", tone_and_style="Test", deliverable="Test",
            timelines="Test", visual_guidelines="Test", cta="Test"
        )

        result = await orchestrator.regenerate_image(
            brief=brief,
            previous_image_prompt="Original prompt",
            modification_request="Make it different",
            products=[]
        )

        assert "image_error" in result
        assert "Content policy" in result["image_error"]


@pytest.mark.asyncio
async def test_get_chat_client_foundry_no_endpoint():
    """Test _get_chat_client in Foundry mode with missing endpoint raises error."""
    with patch("orchestrator.app_settings") as mock_settings, \
         patch("orchestrator.DefaultAzureCredential") as mock_cred, \
         patch("orchestrator.FOUNDRY_AVAILABLE", True):

        mock_settings.ai_foundry.use_foundry = True
        mock_settings.ai_foundry.model_deployment = "gpt-4"
        mock_settings.azure_openai.endpoint = None  # No endpoint
        mock_settings.azure_openai.api_version = "2024-02-15"
        mock_settings.azure_openai.gpt_model = "gpt-4"
        mock_settings.base_settings.azure_client_id = None

        mock_credential = MagicMock()
        mock_credential.get_token.return_value = MagicMock(token="test-token")
        mock_cred.return_value = mock_credential

        orchestrator = ContentGenerationOrchestrator()
        orchestrator._use_foundry = True

        with pytest.raises(ValueError, match="AZURE_OPENAI_ENDPOINT is required"):
            orchestrator._get_chat_client()


@pytest.mark.asyncio
async def test_get_chat_client_direct_no_endpoint():
    """Test _get_chat_client in Direct mode with missing endpoint raises error."""
    with patch("orchestrator.app_settings") as mock_settings, \
         patch("orchestrator.DefaultAzureCredential") as mock_cred:

        mock_settings.ai_foundry.use_foundry = False
        mock_settings.azure_openai.endpoint = None  # No endpoint
        mock_settings.azure_openai.api_version = "2024-02-15"
        mock_settings.azure_openai.gpt_model = "gpt-4"
        mock_settings.base_settings.azure_client_id = None

        mock_credential = MagicMock()
        mock_credential.get_token.return_value = MagicMock(token="test-token")
        mock_cred.return_value = mock_credential

        orchestrator = ContentGenerationOrchestrator()
        orchestrator._use_foundry = False

        with pytest.raises(ValueError, match="AZURE_OPENAI_ENDPOINT is not configured"):
            orchestrator._get_chat_client()
