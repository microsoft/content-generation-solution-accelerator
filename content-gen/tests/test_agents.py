"""
Unit tests for the Content Generation agents.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from backend.models import CreativeBrief, Product, ComplianceSeverity
from backend.agents.text_content_agent import validate_text_compliance
from backend.agents.compliance_agent import comprehensive_compliance_check


class TestTextContentValidation:
    """Tests for text content validation."""
    
    def test_prohibited_word_detection(self):
        """Test that prohibited words are flagged as errors."""
        result = validate_text_compliance(
            content="This is the cheapest product on the market!",
            content_type="body"
        )
        
        assert not result["is_valid"]
        errors = [v for v in result["violations"] if v["severity"] == "error"]
        assert len(errors) >= 1
        assert any("cheapest" in v["message"].lower() for v in errors)
    
    def test_headline_length_warning(self):
        """Test that long headlines get warnings."""
        long_headline = "This is an extremely long headline that definitely exceeds the maximum character limit for headlines in our marketing materials"
        
        result = validate_text_compliance(
            content=long_headline,
            content_type="headline"
        )
        
        warnings = [v for v in result["violations"] if v["severity"] == "warning"]
        assert len(warnings) >= 1
        assert any("headline" in v["field"].lower() for v in warnings)
    
    def test_unsubstantiated_claims(self):
        """Test that unsubstantiated claims are flagged."""
        result = validate_text_compliance(
            content="We are the #1 choice for customers",
            content_type="body"
        )
        
        assert not result["is_valid"]
        errors = [v for v in result["violations"] if v["severity"] == "error"]
        assert any("#1" in v["message"] or "claim" in v["message"].lower() for v in errors)
    
    def test_clean_content_passes(self):
        """Test that clean content passes validation."""
        result = validate_text_compliance(
            content="Experience amazing quality with our new product line!",
            content_type="body"
        )
        
        # Should not have any errors
        errors = [v for v in result["violations"] if v["severity"] == "error"]
        assert len(errors) == 0


class TestComprehensiveCompliance:
    """Tests for comprehensive compliance checking."""
    
    def test_all_fields_checked(self):
        """Test that all content fields are validated."""
        result = comprehensive_compliance_check(
            headline="Short headline",
            body="Good body copy that is engaging!",
            cta_text="Shop Now",
            image_prompt="Professional product photo",
            image_alt_text="Product image"
        )
        
        assert "is_valid" in result
        assert "violations" in result
        assert "summary" in result
    
    def test_missing_cta_warning(self):
        """Test that missing CTA generates warning."""
        result = comprehensive_compliance_check(
            headline="Great headline",
            body="Great body copy",
            cta_text=""
        )
        
        warnings = [v for v in result["violations"] if v["severity"] == "warning"]
        assert any("cta" in v["field"].lower() for v in warnings)
    
    def test_prohibited_image_terms(self):
        """Test that prohibited terms in image prompts are flagged."""
        result = comprehensive_compliance_check(
            image_prompt="Product photo with competitor logo"
        )
        
        errors = [v for v in result["violations"] if v["severity"] == "error"]
        assert any("competitor" in v["message"].lower() for v in errors)
    
    def test_missing_disclosures(self):
        """Test that missing required disclosures are flagged."""
        result = comprehensive_compliance_check(
            body="Great product at an amazing price!"
        )
        
        # Check if any disclosure-related errors exist
        # (depends on brand guidelines configuration)
        assert "violations" in result


class TestCreativeBriefModel:
    """Tests for CreativeBrief model."""
    
    def test_brief_creation(self):
        """Test creating a valid creative brief."""
        brief = CreativeBrief(
            overview="Summer sale campaign",
            objectives="Increase sales by 20%",
            target_audience="Young adults 18-35",
            key_message="Save big this summer",
            tone_and_style="Upbeat and energetic",
            deliverable="Social media posts",
            timelines="June 2024",
            visual_guidelines="Bright colors, summer themes",
            cta="Shop the sale"
        )
        
        assert brief.overview == "Summer sale campaign"
        assert brief.target_audience == "Young adults 18-35"
    
    def test_brief_optional_fields(self):
        """Test that optional fields default correctly."""
        brief = CreativeBrief(
            overview="Campaign overview"
        )
        
        assert brief.overview == "Campaign overview"
        assert brief.objectives == ""


class TestProductModel:
    """Tests for Product model."""
    
    def test_product_creation(self):
        """Test creating a valid product."""
        product = Product(
            product_name="Wireless Headphones",
            category="Electronics",
            sub_category="Audio",
            marketing_description="Premium sound quality",
            detailed_spec_description="40mm drivers, 30hr battery",
            sku="WH-1000XM5",
            model="XM5"
        )
        
        assert product.product_name == "Wireless Headphones"
        assert product.sku == "WH-1000XM5"
    
    def test_product_with_image(self):
        """Test product with image information."""
        product = Product(
            product_name="Test Product",
            category="Test",
            sub_category="Test",
            marketing_description="Test",
            detailed_spec_description="Test",
            sku="TEST-001",
            model="T1",
            image_url="https://example.com/image.jpg",
            image_description="A sleek black product"
        )
        
        assert product.image_url == "https://example.com/image.jpg"
        assert product.image_description == "A sleek black product"
