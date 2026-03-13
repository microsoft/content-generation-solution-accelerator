"""
Routing Service - Message Classification and Intent Detection

This service handles routing of incoming messages to appropriate handlers
based on keywords and conversation state. Mirrors the routing logic
previously implemented in the frontend App.tsx.
"""

import logging
import re
from dataclasses import dataclass
from enum import Enum
from typing import Optional

logger = logging.getLogger(__name__)


class Intent(Enum):
    """Possible message intents for routing."""

    # Brief-related intents
    PARSE_BRIEF = "parse_brief"
    REFINE_BRIEF = "refine_brief"
    CONFIRM_BRIEF = "confirm_brief"

    # Product-related intents
    SEARCH_PRODUCTS = "search_products"

    # Generation-related intents
    GENERATE_CONTENT = "generate_content"
    MODIFY_IMAGE = "modify_image"

    # General intents
    GENERAL_CHAT = "general_chat"
    START_OVER = "start_over"
    CLARIFICATION_RESPONSE = "clarification_response"


@dataclass
class ConversationState:
    """Current state of a conversation, derived from stored data."""

    has_brief: bool = False
    brief_confirmed: bool = False
    has_products: bool = False
    has_generated_content: bool = False
    awaiting_clarification: bool = False
    current_phase: str = "initial"  # initial, brief, products, generation, complete


@dataclass
class RoutingResult:
    """Result of intent classification."""

    intent: Intent
    confidence: float  # 0.0 to 1.0
    action: Optional[str] = None  # Original action if provided
    matched_keywords: list = None

    def __post_init__(self):
        if self.matched_keywords is None:
            self.matched_keywords = []


class RoutingService:
    """
    Service for classifying message intent and routing to appropriate handlers.

    Keywords are matched against user messages to determine intent.
    These keywords mirror the frontend logic that was previously in App.tsx.
    """

    # Keywords indicating user wants to modify or refine something
    REFINEMENT_KEYWORDS = [
        "change", "update", "modify", "add", "remove",
        "delete", "set", "make", "should be"
    ]

    # Keywords indicating image modification intent
    IMAGE_MODIFICATION_KEYWORDS = [
        "change", "modify", "update", "replace", "show", "display",
        "use", "generate", "create", "instead", "different", "another", "make it", "make the",
        "kitchen", "dining", "living", "bedroom", "bathroom",
        "outdoor", "office", "room", "scene", "setting",
        "background", "style", "color", "lighting"
    ]

    # Keywords indicating a brief/campaign description
    BRIEF_KEYWORDS = [
        "campaign", "marketing", "target audience", "objective",
        "deliverable", "promote", "advertise", "create content",
        "social media", "email", "ad", "advertisement"
    ]

    # Keywords indicating product search or selection
    PRODUCT_KEYWORDS = [
        "product", "find", "search", "show me", "look for",
        "paint", "color", "brand"
    ]

    def __init__(self):
        """Initialize the routing service."""
        logger.info("Routing service initialized")

    def classify_intent(
        self,
        message: Optional[str] = None,
        action: Optional[str] = None,
        payload: Optional[dict] = None,
        state: Optional[ConversationState] = None
    ) -> RoutingResult:
        """
        Classify the intent of a message or action.

        Args:
            message: Free text message from user
            action: Explicit action (e.g., "confirm_brief", "select_product")
            payload: Additional data for the action
            state: Current conversation state

        Returns:
            RoutingResult with classified intent
        """
        if state is None:
            state = ConversationState()

        # If explicit action is provided, route directly
        if action:
            return self._classify_action(action, payload)

        # Otherwise, classify based on message + state
        if message:
            return self._classify_message(message, state)

        # No message or action
        return RoutingResult(
            intent=Intent.GENERAL_CHAT,
            confidence=0.0
        )

    def _classify_action(
        self,
        action: str,
        payload: Optional[dict] = None
    ) -> RoutingResult:
        """
        Map explicit action strings to intents.

        Actions come from button clicks in the frontend.
        """
        action_lower = action.lower().strip()

        action_mapping = {
            "confirm_brief": Intent.CONFIRM_BRIEF,
            "generate_content": Intent.GENERATE_CONTENT,
            "start_over": Intent.START_OVER,
            "modify_image": Intent.MODIFY_IMAGE,
        }

        intent = action_mapping.get(action_lower, Intent.GENERAL_CHAT)

        return RoutingResult(
            intent=intent,
            confidence=1.0,  # Explicit actions have full confidence
            action=action
        )

    def _classify_message(
        self,
        message: str,
        state: ConversationState
    ) -> RoutingResult:
        """
        Classify message intent based on keywords and conversation state.

        The classification logic considers:
        1. Keywords in the message
        2. Current conversation phase/state
        3. What the user is likely trying to do
        """
        message_lower = message.lower().strip()

        # Check for awaiting clarification response
        if state.awaiting_clarification:
            return RoutingResult(
                intent=Intent.CLARIFICATION_RESPONSE,
                confidence=0.8
            )

        # Check for image modification (if content exists)
        if state.has_generated_content:
            image_matches = self._find_keyword_matches(
                message_lower,
                self.IMAGE_MODIFICATION_KEYWORDS
            )
            if image_matches:
                return RoutingResult(
                    intent=Intent.MODIFY_IMAGE,
                    confidence=0.9,
                    matched_keywords=image_matches
                )

        # Check for brief refinement (if brief exists but not in generation)
        if state.has_brief and not state.has_generated_content:
            refinement_matches = self._find_keyword_matches(
                message_lower,
                self.REFINEMENT_KEYWORDS
            )
            if refinement_matches:
                return RoutingResult(
                    intent=Intent.REFINE_BRIEF,
                    confidence=0.85,
                    matched_keywords=refinement_matches
                )

        # Check for product search/selection
        product_matches = self._find_keyword_matches(
            message_lower,
            self.PRODUCT_KEYWORDS
        )
        if product_matches and state.brief_confirmed:
            return RoutingResult(
                intent=Intent.SEARCH_PRODUCTS,
                confidence=0.8,
                matched_keywords=product_matches
            )

        # Check for brief/campaign keywords (initial message or new brief)
        brief_matches = self._find_keyword_matches(
            message_lower,
            self.BRIEF_KEYWORDS
        )
        if brief_matches or not state.has_brief:
            # Likely a new brief or elaborating on the campaign
            return RoutingResult(
                intent=Intent.PARSE_BRIEF,
                confidence=0.8 if brief_matches else 0.6,
                matched_keywords=brief_matches
            )

        # Default to general chat
        return RoutingResult(
            intent=Intent.GENERAL_CHAT,
            confidence=0.5
        )

    def _find_keyword_matches(
        self,
        message: str,
        keywords: list
    ) -> list:
        """
        Find which keywords match in the message.

        Args:
            message: Lowercase message to search
            keywords: List of keywords to match

        Returns:
            List of matched keywords
        """
        matches = []
        for keyword in keywords:
            # Use word boundary matching for single words
            # Use simple contains for multi-word phrases
            if " " in keyword:
                if keyword in message:
                    matches.append(keyword)
            else:
                pattern = rf"\b{re.escape(keyword)}\b"
                if re.search(pattern, message, re.IGNORECASE):
                    matches.append(keyword)
        return matches

    def derive_state_from_conversation(
        self,
        conversation: Optional[dict]
    ) -> ConversationState:
        """
        Derive conversation state from stored conversation data.

        Args:
            conversation: Conversation document from CosmosDB

        Returns:
            ConversationState object
        """
        if not conversation:
            return ConversationState()

        brief = conversation.get("brief")
        generated_content = conversation.get("generated_content")
        messages = conversation.get("messages", [])
        metadata = conversation.get("metadata", {})

        # Determine if brief is confirmed
        # Check messages for confirmation indicator
        brief_confirmed = False
        if brief and messages:
            # Look for confirmation signals in metadata or messages
            brief_confirmed = metadata.get("brief_confirmed", False)
            # Also check for product selection (implies brief was confirmed)
            if generated_content or metadata.get("products_selected"):
                brief_confirmed = True

        # Determine if awaiting clarification
        awaiting_clarification = False
        if messages:
            last_assistant_msg = None
            for msg in reversed(messages):
                if msg.get("role") == "assistant":
                    last_assistant_msg = msg
                    break
            if last_assistant_msg:
                content = last_assistant_msg.get("content", "").lower()
                if "?" in content and any(word in content for word in ["please", "could you", "can you", "what", "which"]):
                    awaiting_clarification = True

        # Determine current phase
        if generated_content:
            current_phase = "complete"
        elif metadata.get("products_selected"):
            current_phase = "generation"
        elif brief_confirmed:
            current_phase = "products"
        elif brief:
            current_phase = "brief"
        else:
            current_phase = "initial"

        return ConversationState(
            has_brief=bool(brief),
            brief_confirmed=brief_confirmed,
            has_products=bool(metadata.get("products_selected")),
            has_generated_content=bool(generated_content),
            awaiting_clarification=awaiting_clarification,
            current_phase=current_phase
        )


# Singleton instance
_routing_service: Optional[RoutingService] = None


def get_routing_service() -> RoutingService:
    """Get or create the routing service singleton."""
    global _routing_service
    if _routing_service is None:
        _routing_service = RoutingService()
    return _routing_service
