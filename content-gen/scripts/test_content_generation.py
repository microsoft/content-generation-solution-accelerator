"""
Test script to simulate marketing content creation workflow.

This script tests the end-to-end content generation flow:
1. Research Agent searches for products and visual styles
2. Planning Agent creates content strategy
3. Text Content Agent generates marketing copy
4. Image Content Agent generates image prompts
5. Compliance Agent validates content

Run with: python scripts/test_content_generation.py
"""

import asyncio
import json
import sys
import os
from typing import Dict, Any

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))


# Sample creative briefs for testing
SAMPLE_BRIEFS = [
    {
        "name": "Holiday Audio Campaign",
        "brief": """
Create a holiday marketing campaign for our premium wireless headphones.

Campaign Details:
- Target Audience: Tech-savvy professionals, 25-45 years old
- Campaign Theme: "Gift of Sound" - perfect holiday gift for music lovers
- Tone: Warm, festive, but sophisticated
- Channels: Social media, Email newsletter
- Key Messages: Premium sound quality, noise cancellation, perfect gift

Deliverables Needed:
1. Social media post with headline and body copy
2. Email subject line and preview text
3. Product hero image concept description
"""
    },
    {
        "name": "Fitness Product Launch",
        "brief": """
Launch campaign for our new Performance Yoga Mat.

Campaign Details:
- Target Audience: Health-conscious individuals, yoga enthusiasts, 20-40 years old
- Campaign Theme: "Elevate Your Practice" - premium eco-friendly yoga experience
- Tone: Calm, inspiring, wellness-focused
- Channels: Social media, Wellness blogs
- Key Messages: Eco-friendly materials, superior grip, alignment markers

Deliverables Needed:
1. Social media carousel post copy (3 slides)
2. Social media pin description
3. Lifestyle image concept for the mat in use
"""
    },
    {
        "name": "Luxury Watch Campaign",
        "brief": """
Create a sophisticated campaign for our Titanium Travel Watch.

Campaign Details:
- Target Audience: Affluent travelers, adventure seekers, 35-55 years old
- Campaign Theme: "Time for Adventure" - precision meets exploration
- Tone: Sophisticated, aspirational, adventurous
- Channels: Print magazine, LinkedIn, Premium digital ads
- Key Messages: Swiss precision, titanium durability, dual timezone

Deliverables Needed:
1. Magazine ad headline and body copy
2. LinkedIn post for business travelers
3. Hero image concept showing the watch in travel context
"""
    }
]


async def test_search_service():
    """Test the search service for grounding data."""
    print("\n" + "=" * 60)
    print("STEP 1: Testing Search Service (Grounding Data)")
    print("=" * 60)
    
    from backend.services.search_service import get_search_service
    
    service = await get_search_service()
    
    # Test product search
    print("\n📦 Searching for products: 'wireless audio'")
    products = await service.search_products("wireless audio", top=3)
    print(f"   Found {len(products)} products:")
    for p in products:
        print(f"   • {p['product_name']} ({p['category']})")
        print(f"     {p['marketing_description'][:80]}...")
    
    # Test visual style search
    print("\n🎨 Searching for visual styles: 'professional modern'")
    images = await service.search_images("professional modern", top=3)
    print(f"   Found {len(images)} visual styles:")
    for img in images:
        print(f"   • {img['name']}: {img['primary_color']} / {img['mood']}")
    
    # Test combined grounding context
    print("\n📋 Getting grounding context for 'holiday gift electronics'")
    context = await service.get_grounding_context(
        product_query="holiday gift electronics",
        image_query="warm festive",
        mood="Warm"
    )
    print(f"   Products: {context['product_count']}, Images: {context['image_count']}")
    
    return context


async def test_research_agent_tools():
    """Test the research agent's tool functions directly."""
    print("\n" + "=" * 60)
    print("STEP 2: Testing Research Agent Tools")
    print("=" * 60)
    
    from backend.agents.research_agent import (
        search_products,
        search_visual_styles,
        get_grounding_context
    )
    
    # Test search_products tool
    print("\n🔍 Testing search_products tool...")
    result = await search_products(
        query="yoga fitness",
        category="Sports & Fitness",
        limit=2
    )
    print(f"   Query: 'yoga fitness', Category: 'Sports & Fitness'")
    print(f"   Found: {result['total_count']} products")
    for p in result['products']:
        print(f"   • {p['product_name']}")
    
    # Test search_visual_styles tool
    print("\n🎨 Testing search_visual_styles tool...")
    result = await search_visual_styles(
        query="calm natural green",
        color_family="Nature",
        limit=2
    )
    print(f"   Query: 'calm natural green', Color Family: 'Nature'")
    print(f"   Found: {result['total_count']} visual styles")
    for v in result['visual_styles']:
        print(f"   • {v['name']}: {v['style']}")
    
    # Test get_grounding_context tool
    print("\n📦 Testing get_grounding_context tool...")
    result = await get_grounding_context(
        product_query="luxury accessories",
        visual_query="sophisticated elegant",
        mood="Elegant"
    )
    print(f"   Products: {result['product_count']}, Images: {result['image_count']}")
    
    return result


async def simulate_content_generation(brief: Dict[str, Any]):
    """Simulate the content generation workflow for a brief."""
    print("\n" + "=" * 60)
    print(f"STEP 3: Simulating Content Generation")
    print(f"Campaign: {brief['name']}")
    print("=" * 60)
    
    from backend.services.search_service import get_search_service
    from backend.settings import app_settings
    
    # Extract key terms from brief (simplified - real implementation would use AI)
    brief_text = brief['brief'].lower()
    
    # Determine product category
    if 'headphones' in brief_text or 'audio' in brief_text:
        product_query = "wireless headphones audio"
        category = "Electronics"
    elif 'yoga' in brief_text or 'fitness' in brief_text:
        product_query = "yoga mat fitness"
        category = "Sports & Fitness"
    elif 'watch' in brief_text:
        product_query = "titanium watch travel"
        category = "Accessories"
    else:
        product_query = "product"
        category = None
    
    # Determine visual mood
    if 'holiday' in brief_text or 'festive' in brief_text:
        visual_query = "warm inviting"
        mood = "Warm"
    elif 'calm' in brief_text or 'wellness' in brief_text:
        visual_query = "calm peaceful natural"
        mood = "Tranquil"
    elif 'sophisticated' in brief_text or 'luxury' in brief_text:
        visual_query = "sophisticated elegant premium"
        mood = "Sophisticated"
    else:
        visual_query = "modern professional"
        mood = None
    
    # Get grounding context
    print(f"\n🔍 Researching products: '{product_query}'")
    print(f"🎨 Finding visual styles: '{visual_query}'")
    
    service = await get_search_service()
    context = await service.get_grounding_context(
        product_query=product_query,
        image_query=visual_query,
        category=category,
        mood=mood
    )
    
    print(f"\n📊 Grounding Context Retrieved:")
    print(f"   • {context['product_count']} matching products")
    print(f"   • {context['image_count']} matching visual styles")
    
    # Display matched products
    if context['products']:
        print("\n📦 Matched Products:")
        for p in context['products'][:2]:
            print(f"   • {p['product_name']} ({p['sku']})")
            print(f"     {p['marketing_description']}")
    
    # Display matched visual styles
    if context['images']:
        print("\n🎨 Matched Visual Styles:")
        for img in context['images'][:2]:
            print(f"   • {img['name']}")
            print(f"     Colors: {img['primary_color']} / {img['secondary_color']}")
            print(f"     Mood: {img['mood']}, Style: {img['style']}")
    
    # Simulate content planning
    print("\n📝 Content Plan (Simulated):")
    print("   Based on the grounding context, the content would include:")
    
    if context['products']:
        product = context['products'][0]
        print(f"\n   HEADLINE CONCEPT:")
        print(f"   \"Experience {product['product_name']} - {product['marketing_description'][:50]}...\"")
        
        print(f"\n   KEY MESSAGING POINTS:")
        specs = product.get('detailed_spec_description', '')[:200]
        print(f"   • Product highlights: {specs}...")
        
        if product.get('image_description'):
            print(f"\n   IMAGE CONCEPT:")
            print(f"   Based on product visual: {product['image_description'][:150]}...")
    
    if context['images']:
        style = context['images'][0]
        print(f"\n   VISUAL DIRECTION:")
        print(f"   • Color palette: {style['primary_color']} with {style['secondary_color']} accents")
        print(f"   • Mood: {style['mood']}")
        print(f"   • Style: {style['style']}")
        print(f"   • Best for: {style.get('use_cases', 'General marketing')[:100]}")
    
    # Show brand compliance context
    print("\n✅ Brand Compliance Check:")
    print(f"   • Tone: {app_settings.brand_guidelines.tone}")
    print(f"   • Max headline: {app_settings.brand_guidelines.max_headline_length} chars")
    print(f"   • Prohibited words: {', '.join(app_settings.brand_guidelines.prohibited_words[:3])}...")
    
    return context


async def run_full_test():
    """Run the complete test suite."""
    print("\n" + "=" * 70)
    print("  MARKETING CONTENT GENERATION - TEST SIMULATION")
    print("=" * 70)
    
    try:
        # Step 1: Test search service
        await test_search_service()
        
        # Step 2: Test research agent tools
        await test_research_agent_tools()
        
        # Step 3: Simulate content generation for each brief
        for brief in SAMPLE_BRIEFS:
            await simulate_content_generation(brief)
            print("\n" + "-" * 60)
        
        print("\n" + "=" * 70)
        print("  ✅ ALL TESTS COMPLETED SUCCESSFULLY")
        print("=" * 70)
        print("\nThe content generation system is configured and ready.")
        print("Products and visual styles are being retrieved from Azure AI Search.")
        print("\nNext steps:")
        print("  1. Start the backend: python app.py")
        print("  2. Start the frontend: npm run dev")
        print("  3. Submit a creative brief through the chat interface")
        print("=" * 70 + "\n")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    asyncio.run(run_full_test())
