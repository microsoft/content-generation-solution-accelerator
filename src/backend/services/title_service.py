"""
Title Generation Service - Generates concise conversation titles using AI.

This service provides a dedicated agent for generating meaningful,
short titles for chat conversations based on the user's first message.

Supports both Azure AI Foundry mode (pre-created agents) and
Azure OpenAI Direct mode (in-memory agents).
"""

import logging
import re
from typing import Optional

from agent_framework.azure import AzureOpenAIResponsesClient, AzureAIProjectAgentProvider
from azure.identity import DefaultAzureCredential
from azure.identity.aio import DefaultAzureCredential as AsyncDefaultAzureCredential

from settings import app_settings

logger = logging.getLogger(__name__)

# Title generation instructions (from MS reference accelerator)
TITLE_INSTRUCTIONS = """Summarize the conversation so far into a 4-word or less title.
Do not use any quotation marks or punctuation.
Do not include any other commentary or description."""


class TitleService:
    """Service for generating conversation titles using AI."""

    def __init__(self):
        self._agent = None
        self._initialized = False
        self._use_foundry = app_settings.ai_foundry.use_foundry
        self._provider = None  # AzureAIProjectAgentProvider (Foundry mode only)

    async def initialize(self) -> None:
        """Initialize the title generation agent.

        Foundry mode: retrieves pre-created TitleAgent via
        AzureAIProjectAgentProvider.get_agent(name=...).

        Direct mode: creates in-memory agent via
        AzureOpenAIResponsesClient.as_agent(name=..., instructions=...).
        """
        if self._initialized:
            return

        try:
            if self._use_foundry:
                # --- Foundry mode: retrieve pre-created TitleAgent ---
                project_endpoint = app_settings.ai_foundry.project_endpoint
                if not project_endpoint:
                    logger.warning("Title service: AZURE_AI_PROJECT_ENDPOINT not configured, using fallback")
                    return

                agent_name = app_settings.ai_foundry.agent_names.get("title")
                if not agent_name:
                    logger.warning("Title service: AGENT_NAME_TITLE not configured, using fallback")
                    return

                async_credential = AsyncDefaultAzureCredential()
                self._provider = AzureAIProjectAgentProvider(
                    project_endpoint=project_endpoint,
                    credential=async_credential,
                )

                logger.info(f"Retrieving TitleAgent from Foundry project: {agent_name}")
                self._agent = await self._provider.get_agent(name=agent_name)
                logger.info("TitleAgent retrieved from Foundry project")

            else:
                # --- Direct mode: create in-memory agent ---
                endpoint = app_settings.azure_openai.endpoint
                if not endpoint:
                    logger.warning("Title service: Azure OpenAI endpoint not configured, using fallback")
                    return

                deployment = app_settings.azure_openai.gpt_model
                api_version = app_settings.azure_openai.api_version

                credential = DefaultAzureCredential()
                chat_client = AzureOpenAIResponsesClient(
                    endpoint=endpoint,
                    deployment_name=deployment,
                    api_version=api_version,
                    credential=credential,
                )

                self._agent = chat_client.as_agent(
                    name="title_agent",
                    instructions=TITLE_INSTRUCTIONS,
                )
                logger.info("TitleAgent created in Direct mode")

            self._initialized = True

        except Exception as e:
            logger.exception(f"Failed to initialize title service: {e}")
            self._agent = None

    @staticmethod
    def _fallback_title(message: str) -> str:
        """Generate a fallback title using first 4 words of the message."""
        if not message or not message.strip():
            return "New Conversation"
        words = message.strip().split()[:4]
        return " ".join(words) if words else "New Conversation"

    async def generate_title(self, first_user_message: str) -> str:
        """
        Generate a concise conversation title from the first user message.

        Args:
            first_user_message: The user's first message in the conversation

        Returns:
            A short, meaningful title (max 4 words)
        """
        if not first_user_message or not first_user_message.strip():
            return "New Conversation"

        if not self._initialized:
            await self.initialize()

        if self._agent is None:
            logger.warning("Title generation: agent not available, using fallback")
            return self._fallback_title(first_user_message)

        prompt = (
            "Create a concise chat title for this user request.\n"
            "Respond with title only.\n\n"
            f"User request: {first_user_message.strip()}"
        )

        try:
            response = await self._agent.run(prompt)

            # Clean up the response
            title = str(response).strip().splitlines()[0].strip()
            title = re.sub(r"\s+", " ", title)
            title = re.sub(r"[\"'`]+", "", title)
            title = re.sub(r"[.,!?;:]+", "", title).strip()

            if not title:
                logger.warning("Title generation: agent returned empty, using fallback")
                return self._fallback_title(first_user_message)

            final_title = " ".join(title.split()[:4])
            return final_title

        except Exception as exc:
            logger.exception("Failed to generate conversation title: %s", exc)
            return self._fallback_title(first_user_message)


# Singleton instance
_title_service: Optional[TitleService] = None


def get_title_service() -> TitleService:
    """Get or create the singleton title service instance.

    Note: initialize() is async and is called lazily by generate_title()
    on first use.
    """
    global _title_service
    if _title_service is None:
        _title_service = TitleService()
    return _title_service
