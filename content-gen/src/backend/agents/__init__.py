"""Agents package for Content Generation Solution Accelerator.

The multi-agent workflow is handled by the orchestrator using Microsoft Agent Framework.
This package provides utility functions used by the orchestrator.
"""

from agents.image_content_agent import generate_dalle_image, generate_image

__all__ = [
    "generate_dalle_image",
    "generate_image",
]
