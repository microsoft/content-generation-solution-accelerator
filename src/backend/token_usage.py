"""
Token usage tracking for the Content Generation orchestrator.

Captures LLM token usage from Microsoft Agent Framework agent runs and workflow
streams (Azure OpenAI / Azure AI Foundry) and emits per-agent and per-model
custom events to Application Insights via ``event_utils.track_event_if_configured``.

Usage:
    from token_usage import TokenUsageAccumulator, extract_usage_from_response

    acc = TokenUsageAccumulator(user_id="abc", conversation_id="xyz",
                                agent_model_map={"planning_agent": "gpt-5"})
    response = await agent.run(prompt)
    acc.record_response(agent_name="planning_agent", response=response)
    acc.flush()  # emits LLM_*_Token_Usage events
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Iterable, Optional

from event_utils import track_event_if_configured

logger = logging.getLogger(__name__)

# Custom Application Insights event names (shared with KQL dashboard queries).
EVENT_SUMMARY = "LLM_Token_Usage_Summary"
EVENT_AGENT = "LLM_Agent_Token_Usage"
EVENT_MODEL = "LLM_Model_Token_Usage"


@dataclass(slots=True)
class _Counts:
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    model_deployment_name: str = ""

    def add(self, inp: int, out: int, tot: int) -> None:
        self.input_tokens += inp
        self.output_tokens += out
        self.total_tokens += tot


def _coerce_int(value: Any) -> int:
    try:
        if value is None:
            return 0
        return int(value)
    except (TypeError, ValueError):
        return 0


def _from_dict(d: dict) -> Optional[tuple[int, int, int]]:
    """Pull (input, output, total) out of a usage-shaped dict.

    Handles both the Microsoft Agent Framework ``UsageDetails`` shape
    (``input_token_count`` / ``output_token_count`` / ``total_token_count``)
    and the OpenAI SDK shape (``prompt_tokens`` / ``completion_tokens`` /
    ``total_tokens``).
    """
    inp = _coerce_int(
        d.get("input_token_count")
        or d.get("prompt_tokens")
        or d.get("input_tokens")
    )
    out = _coerce_int(
        d.get("output_token_count")
        or d.get("completion_tokens")
        or d.get("output_tokens")
    )
    tot = _coerce_int(d.get("total_token_count") or d.get("total_tokens")) or (
        inp + out
    )
    if tot <= 0:
        return None
    return (inp, out, tot)


def _from_usage_details(details: Any) -> Optional[tuple[int, int, int]]:
    """Extract counts from a ``UsageDetails`` object, dict, or similar."""
    if details is None:
        return None
    if isinstance(details, dict):
        return _from_dict(details)
    inp = _coerce_int(
        getattr(details, "input_token_count", None)
        or getattr(details, "prompt_tokens", None)
        or getattr(details, "input_tokens", None)
    )
    out = _coerce_int(
        getattr(details, "output_token_count", None)
        or getattr(details, "completion_tokens", None)
        or getattr(details, "output_tokens", None)
    )
    tot = _coerce_int(
        getattr(details, "total_token_count", None)
        or getattr(details, "total_tokens", None)
    ) or (inp + out)
    if tot <= 0:
        return None
    return (inp, out, tot)


def _scan_contents(contents: Optional[Iterable]) -> Optional[tuple[int, int, int]]:
    """Look for ``UsageContent`` entries in a contents list."""
    if not contents:
        return None
    for item in contents:
        # Framework UsageContent: has .details (UsageDetails)
        details = getattr(item, "details", None)
        if details is not None:
            result = _from_usage_details(details)
            if result:
                return result
        # Some shapes expose .usage_details directly
        usage_details = getattr(item, "usage_details", None)
        if usage_details is not None:
            result = _from_usage_details(usage_details)
            if result:
                return result
        # Plain dict content
        if isinstance(item, dict):
            if isinstance(item.get("details"), dict):
                result = _from_dict(item["details"])
                if result:
                    return result
            if isinstance(item.get("usage_details"), dict):
                result = _from_dict(item["usage_details"])
                if result:
                    return result
    return None


def extract_usage_from_response(response: Any) -> Optional[tuple[int, int, int]]:
    """Extract ``(input, output, total)`` token counts from an ``AgentResponse``.

    Checks (in order):
        1. ``response.usage_details``
        2. ``response.messages[*].contents[*]`` for ``UsageContent`` items
        3. ``response.raw_representation.usage`` (OpenAI SDK fallback)
    Returns ``None`` if no usage information is present.
    """
    if response is None:
        return None

    result = _from_usage_details(getattr(response, "usage_details", None))
    if result:
        return result

    messages = getattr(response, "messages", None) or []
    for msg in messages:
        result = _scan_contents(getattr(msg, "contents", None))
        if result:
            return result

    raw = getattr(response, "raw_representation", None)
    if raw is not None:
        usage = getattr(raw, "usage", None) or (
            raw.get("usage") if isinstance(raw, dict) else None
        )
        if usage is not None:
            result = _from_usage_details(usage)
            if result:
                return result
    return None


def extract_usage_from_update(update: Any) -> Optional[tuple[int, int, int]]:
    """Extract token counts from a streaming ``AgentResponseUpdate``."""
    if update is None:
        return None

    result = _scan_contents(getattr(update, "contents", None))
    if result:
        return result

    raw = getattr(update, "raw_representation", None)
    if raw is not None:
        usage = getattr(raw, "usage", None) or (
            raw.get("usage") if isinstance(raw, dict) else None
        )
        if usage is not None:
            result = _from_usage_details(usage)
            if result:
                return result
    return None


def extract_usage_from_event(event: Any) -> tuple[Optional[str], Optional[tuple[int, int, int]]]:
    """Extract ``(executor_id, usage_tuple)`` from a workflow stream event.

    Used while iterating ``workflow.run_stream(...)``: returns the executor /
    agent name plus the usage tuple when present, or ``(None, None)`` for
    unrelated events.
    """
    if event is None:
        return (None, None)

    executor_id = getattr(event, "executor_id", None)
    data = getattr(event, "data", None)
    if data is None:
        return (executor_id, None)

    # AgentRunUpdateEvent → data is AgentResponseUpdate
    usage = extract_usage_from_update(data)
    if usage:
        return (executor_id, usage)

    # AgentRunEvent → data is AgentResponse
    usage = extract_usage_from_response(data)
    if usage:
        return (executor_id, usage)

    return (executor_id, None)


class TokenUsageAccumulator:
    """Accumulates per-agent and per-model token usage for a single request.

    Call ``record_*`` as agent invocations complete, then ``flush()`` once at
    the end of the request to emit Application Insights custom events.
    Telemetry failures are logged but never raised — never break the user
    flow on a telemetry error.
    """

    __slots__ = (
        "user_id",
        "conversation_id",
        "agent_model_map",
        "default_model",
        "by_agent",
        "by_model",
        "totals",
    )

    def __init__(
        self,
        *,
        user_id: str = "",
        conversation_id: str = "",
        agent_model_map: Optional[dict[str, str]] = None,
        default_model: str = "",
    ) -> None:
        self.user_id = user_id or ""
        self.conversation_id = conversation_id or ""
        self.agent_model_map: dict[str, str] = dict(agent_model_map or {})
        self.default_model = default_model or ""
        self.by_agent: dict[str, _Counts] = {}
        self.by_model: dict[str, _Counts] = {}
        self.totals: _Counts = _Counts()

    def _resolve_model(self, agent_name: str) -> str:
        return (
            self.agent_model_map.get(agent_name)
            or self.agent_model_map.get(agent_name or "", "")
            or self.default_model
        )

    def record(self, agent_name: str, usage: Optional[tuple[int, int, int]]) -> None:
        """Record an extracted usage tuple for the named agent (no-op if None/zero)."""
        if not usage:
            return
        inp, out, tot = usage
        if tot <= 0:
            return
        agent = agent_name or "unknown_agent"
        model = self._resolve_model(agent)

        agent_counts = self.by_agent.setdefault(
            agent, _Counts(model_deployment_name=model)
        )
        if not agent_counts.model_deployment_name and model:
            agent_counts.model_deployment_name = model
        agent_counts.add(inp, out, tot)

        if model:
            self.by_model.setdefault(model, _Counts()).add(inp, out, tot)

        self.totals.add(inp, out, tot)

    def record_response(self, *, agent_name: str, response: Any) -> bool:
        """Extract usage from an ``AgentResponse`` and record it. Returns True on success."""
        usage = extract_usage_from_response(response)
        if usage:
            self.record(agent_name, usage)
            return True
        return False

    def record_update(self, *, executor_id: str, update: Any) -> bool:
        """Extract usage from an ``AgentResponseUpdate`` and record it."""
        usage = extract_usage_from_update(update)
        if usage:
            self.record(executor_id, usage)
            return True
        return False

    def record_event(self, event: Any) -> bool:
        """Extract usage from a workflow ``run_stream`` event and record it."""
        executor_id, usage = extract_usage_from_event(event)
        if usage and executor_id:
            self.record(executor_id, usage)
            return True
        return False

    def record_image_api_response(
        self, *, agent_name: str, response_json: Optional[dict], model: str = ""
    ) -> bool:
        """Record token usage from an image-generation REST response (OpenAI shape)."""
        if not isinstance(response_json, dict):
            return False
        usage = response_json.get("usage")
        if not isinstance(usage, dict):
            return False
        if model and agent_name not in self.agent_model_map:
            self.agent_model_map[agent_name] = model
        result = _from_dict(usage)
        if result:
            self.record(agent_name, result)
            return True
        return False

    def has_data(self) -> bool:
        return self.totals.total_tokens > 0

    def flush(self, *, source: str = "") -> None:
        """Emit aggregated events to Application Insights. Safe to call once per request."""
        if not self.has_data():
            return

        base_dims = {
            "user_id": self.user_id,
            "conversation_id": self.conversation_id,
            "source": source,
        }

        try:
            track_event_if_configured(
                EVENT_SUMMARY,
                {
                    **base_dims,
                    "total_input_tokens": str(self.totals.input_tokens),
                    "total_output_tokens": str(self.totals.output_tokens),
                    "total_tokens": str(self.totals.total_tokens),
                    "agent_count": str(len(self.by_agent)),
                    "model_count": str(len(self.by_model)),
                },
            )
        except Exception as e:
            logger.warning("Failed to emit %s: %s", EVENT_SUMMARY, e)

        for agent_name, c in self.by_agent.items():
            try:
                track_event_if_configured(
                    EVENT_AGENT,
                    {
                        **base_dims,
                        "agent_name": agent_name,
                        "model_deployment_name": c.model_deployment_name or self.default_model,
                        "input_tokens": str(c.input_tokens),
                        "output_tokens": str(c.output_tokens),
                        "total_tokens": str(c.total_tokens),
                    },
                )
            except Exception as e:
                logger.warning("Failed to emit %s for %s: %s", EVENT_AGENT, agent_name, e)

        for model_name, c in self.by_model.items():
            try:
                track_event_if_configured(
                    EVENT_MODEL,
                    {
                        **base_dims,
                        "model_deployment_name": model_name,
                        "input_tokens": str(c.input_tokens),
                        "output_tokens": str(c.output_tokens),
                        "total_tokens": str(c.total_tokens),
                    },
                )
            except Exception as e:
                logger.warning("Failed to emit %s for %s: %s", EVENT_MODEL, model_name, e)

        logger.info(
            "[TOKEN USAGE] source=%s user=%s conv=%s total=%d (in=%d, out=%d) "
            "agents=%s models=%s",
            source,
            self.user_id,
            self.conversation_id,
            self.totals.total_tokens,
            self.totals.input_tokens,
            self.totals.output_tokens,
            {k: v.total_tokens for k, v in self.by_agent.items()},
            {k: v.total_tokens for k, v in self.by_model.items()},
        )
