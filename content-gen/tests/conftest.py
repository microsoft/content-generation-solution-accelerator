"""
Pytest configuration for Content Generation tests.
"""

import pytest
import asyncio


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def sample_creative_brief():
    """Sample creative brief for testing."""
    return {
        "overview": "Summer Sale 2024 Campaign",
        "objectives": "Increase online sales by 25% during the summer season",
        "target_audience": "Young professionals aged 25-40 interested in premium electronics",
        "key_message": "Experience premium quality at unbeatable summer prices",
        "tone_and_style": "Upbeat, modern, and aspirational",
        "deliverable": "Social media carousel posts and email banners",
        "timelines": "Campaign runs June 1 - August 31, 2024",
        "visual_guidelines": "Use bright summer colors, outdoor settings, lifestyle imagery",
        "cta": "Shop Now"
    }


@pytest.fixture
def sample_product():
    """Sample product for testing."""
    return {
        "product_name": "ProMax Wireless Headphones",
        "category": "Electronics",
        "sub_category": "Audio",
        "marketing_description": "Immerse yourself in crystal-clear sound with our flagship wireless headphones.",
        "detailed_spec_description": "40mm custom drivers, Active Noise Cancellation, 30-hour battery life, Bluetooth 5.2, USB-C fast charging",
        "sku": "PM-WH-001",
        "model": "ProMax-2024",
        "image_url": "https://example.com/images/headphones.jpg",
        "image_description": "Sleek over-ear headphones in matte black with silver accents, featuring cushioned ear cups and an adjustable headband"
    }


@pytest.fixture
def sample_products():
    """Multiple sample products for testing."""
    return [
        {
            "product_name": "ProMax Wireless Headphones",
            "category": "Electronics",
            "sub_category": "Audio",
            "marketing_description": "Premium wireless audio experience",
            "detailed_spec_description": "40mm drivers, ANC, 30hr battery",
            "sku": "PM-WH-001",
            "model": "ProMax-2024"
        },
        {
            "product_name": "UltraSound Earbuds",
            "category": "Electronics",
            "sub_category": "Audio",
            "marketing_description": "Compact, powerful, always ready",
            "detailed_spec_description": "10mm drivers, 8hr battery, IPX4",
            "sku": "US-EB-002",
            "model": "UltraSound-Mini"
        },
        {
            "product_name": "SoundBar Pro",
            "category": "Electronics",
            "sub_category": "Audio",
            "marketing_description": "Cinema sound for your home",
            "detailed_spec_description": "5.1 surround, 400W, Dolby Atmos",
            "sku": "SB-PRO-003",
            "model": "SoundBar-2024"
        }
    ]


@pytest.fixture
def sample_violations():
    """Sample compliance violations for testing."""
    return [
        {
            "severity": "error",
            "message": "Prohibited word 'guaranteed' found",
            "suggestion": "Remove or replace with 'backed by our promise'",
            "field": "body"
        },
        {
            "severity": "warning",
            "message": "Headline exceeds 80 characters",
            "suggestion": "Shorten to improve readability",
            "field": "headline"
        },
        {
            "severity": "info",
            "message": "Consider adding more engaging punctuation",
            "suggestion": "Add questions or exclamations",
            "field": "body"
        }
    ]
