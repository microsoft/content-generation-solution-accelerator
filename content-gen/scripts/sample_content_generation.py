#!/usr/bin/env python3
"""
Sample Content Generation Script

This script demonstrates how to use the ContentOrchestrator to generate
complete marketing content packages including text and images.

Prerequisites:
1. Set up environment variables (or use a .env file):
   - AZURE_OPENAI_ENDPOINT: Your Azure OpenAI endpoint
   - AZURE_OPENAI_GPT_MODEL: GPT model deployment name
   - AZURE_OPENAI_GPT_IMAGE_ENDPOINT: (Optional) Endpoint for images
   - AZURE_OPENAI_IMAGE_MODEL: Image model name (e.g., gpt-image-1)
   - AZURE_COSMOS_ENDPOINT: Your CosmosDB endpoint
   - AZURE_COSMOS_DATABASE_NAME: content-generation
   - AZURE_COSMOS_CONVERSATIONS_CONTAINER: conversations
   
2. Ensure you have RBAC access:
   - "Cognitive Services OpenAI User" role on the Azure OpenAI resource
   - "Cosmos DB Built-in Data Contributor" on CosmosDB (if using products)

Usage:
    python sample_content_generation.py
    python sample_content_generation.py --no-images
    python sample_content_generation.py --output results.json
"""

import asyncio
import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path

# Add the backend directory to the path
backend_path = Path(__file__).parent.parent / "src" / "backend"
sys.path.insert(0, str(backend_path))

# Now import the orchestrator and models
from orchestrator import ContentOrchestrator
from models import CreativeBrief


def create_sample_brief() -> CreativeBrief:
    """Create a sample creative brief for testing."""
    return CreativeBrief(
        overview="Spring home refresh campaign promoting interior paint colors",
        objectives="Drive awareness and consideration for spring paint collection, increase website traffic by 20%",
        target_audience="Homeowners aged 30-55, interested in DIY home improvement and interior design",
        key_message="Transform your home this spring with our fresh, on-trend paint colors that bring warmth and style to any room",
        tone_and_style="Inspiring, approachable, and aspirational. Use warm, inviting language that speaks to the joy of home improvement",
        deliverable="Social media carousel post (3-5 images) with captions for social media",
        timelines="Launch by March 15th for spring campaign",
        visual_guidelines="Bright, airy rooms with natural lighting. Show before/after transformations. Feature paint swatches in context. Modern, clean aesthetic",
        cta="Shop the Spring Collection - Visit our website for color inspiration",
        raw_input="Sample brief for testing content generation"
    )


def create_sample_products() -> list:
    """Create sample product data for testing."""
    return [
        {
            "id": "sample-1",
            "product_name": "Morning Mist",
            "description": "A soft, ethereal blue-gray that evokes early morning calm. Perfect for bedrooms and living spaces.",
            "tags": "blue, gray, soft, calming, bedroom, living room",
            "price": 45.99,
            "image_url": "https://example.com/morning-mist.jpg"
        },
        {
            "id": "sample-2", 
            "product_name": "Sunlit Meadow",
            "description": "A warm, golden yellow that brings sunshine indoors. Ideal for kitchens and breakfast nooks.",
            "tags": "yellow, warm, sunny, kitchen, cheerful",
            "price": 42.99,
            "image_url": "https://example.com/sunlit-meadow.jpg"
        },
        {
            "id": "sample-3",
            "product_name": "Forest Haven",
            "description": "A rich, deep green inspired by lush forest canopies. Creates a sophisticated, grounding atmosphere.",
            "tags": "green, deep, sophisticated, nature, accent wall",
            "price": 48.99,
            "image_url": "https://example.com/forest-haven.jpg"
        }
    ]


async def generate_content_sample(
    brief: CreativeBrief = None,
    products: list = None,
    generate_images: bool = True,
    output_path: str = None
) -> dict:
    """
    Generate a complete content package using the orchestrator.
    
    Args:
        brief: Creative brief (uses sample if not provided)
        products: Products to feature (uses samples if not provided)
        generate_images: Whether to generate images
        output_path: Path to save results JSON (optional)
    
    Returns:
        Dictionary with generation results
    """
    # Use defaults if not provided
    brief = brief or create_sample_brief()
    products = products or create_sample_products()
    
    print(f"\n{'='*70}")
    print("CONTENT GENERATION SAMPLE")
    print(f"{'='*70}")
    print(f"\nCreative Brief Overview: {brief.overview}")
    print(f"Target Audience: {brief.target_audience}")
    print(f"Deliverable: {brief.deliverable}")
    print(f"Products: {len(products)} items")
    print(f"Generate Images: {generate_images}")
    
    print(f"\n{'='*70}")
    print("Initializing Content Orchestrator...")
    print(f"{'='*70}\n")
    
    # Create and initialize the orchestrator
    orchestrator = ContentOrchestrator()
    orchestrator.initialize()
    
    print("Orchestrator initialized successfully!")
    print("\nGenerating content...\n")
    
    # Generate the content
    start_time = datetime.now()
    
    results = await orchestrator.generate_content(
        brief=brief,
        products=products,
        generate_images=generate_images
    )
    
    elapsed = (datetime.now() - start_time).total_seconds()
    
    # Display results
    print(f"\n{'='*70}")
    print("GENERATION RESULTS")
    print(f"{'='*70}")
    print(f"\nTime elapsed: {elapsed:.1f} seconds")
    
    # Text content
    if results.get("text_content"):
        print(f"\n{'─'*40}")
        print("TEXT CONTENT:")
        print(f"{'─'*40}")
        text_content = results["text_content"]
        # Show first 1000 chars
        if len(text_content) > 1000:
            print(text_content[:1000] + "\n\n[...truncated...]")
        else:
            print(text_content)
    
    # Image prompt
    if results.get("image_prompt"):
        print(f"\n{'─'*40}")
        print("IMAGE PROMPT:")
        print(f"{'─'*40}")
        print(results["image_prompt"][:500] + "..." if len(results.get("image_prompt", "")) > 500 else results["image_prompt"])
    
    # Generated image
    if results.get("generated_image"):
        print(f"\n{'─'*40}")
        print("GENERATED IMAGE:")
        print(f"{'─'*40}")
        img = results["generated_image"]
        if img.get("success"):
            print(f"✅ Image generated successfully")
            print(f"   Model: {img.get('model', 'unknown')}")
            if img.get("image_base64"):
                print(f"   Data size: {len(img['image_base64']) / 1024:.1f} KB (base64)")
        else:
            print(f"❌ Image generation failed: {img.get('error', 'unknown error')}")
    
    # Compliance
    if results.get("compliance"):
        print(f"\n{'─'*40}")
        print("COMPLIANCE CHECK:")
        print(f"{'─'*40}")
        print(results["compliance"])
    
    if results.get("violations"):
        print(f"\n⚠️ Violations found: {len(results['violations'])}")
        for v in results["violations"]:
            print(f"   - {v}")
    
    if results.get("requires_modification"):
        print("\n⚠️ Content requires modification before publishing")
    
    # Save results if output path provided
    if output_path:
        # Prepare results for JSON serialization
        output_data = {
            "timestamp": datetime.now().isoformat(),
            "elapsed_seconds": elapsed,
            "brief": brief.model_dump(),
            "products": products,
            "generate_images": generate_images,
            "results": {
                "text_content": results.get("text_content"),
                "image_prompt": results.get("image_prompt"),
                "compliance": results.get("compliance"),
                "violations": results.get("violations"),
                "requires_modification": results.get("requires_modification"),
            }
        }
        
        # Handle generated image separately (base64 can be large)
        if results.get("generated_image"):
            img = results["generated_image"]
            output_data["results"]["generated_image"] = {
                "success": img.get("success"),
                "model": img.get("model"),
                "error": img.get("error"),
                "revised_prompt": img.get("revised_prompt"),
                # Store base64 in separate file to keep JSON readable
                "has_image_data": bool(img.get("image_base64"))
            }
            
            # Save image to separate file if successful
            if img.get("success") and img.get("image_base64"):
                import base64
                image_path = output_path.replace(".json", "_image.png")
                image_data = base64.b64decode(img["image_base64"])
                with open(image_path, "wb") as f:
                    f.write(image_data)
                output_data["results"]["generated_image"]["image_file"] = image_path
                print(f"\n📁 Image saved to: {image_path}")
        
        with open(output_path, "w") as f:
            json.dump(output_data, f, indent=2)
        print(f"📁 Results saved to: {output_path}")
    
    return results


async def main():
    """Main entry point for the sample script."""
    parser = argparse.ArgumentParser(
        description="Generate marketing content using the Content Orchestrator"
    )
    parser.add_argument(
        "--no-images",
        action="store_true",
        help="Skip image generation"
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        default=None,
        help="Output file path for results JSON"
    )
    parser.add_argument(
        "--brief-file",
        type=str,
        default=None,
        help="Path to JSON file containing creative brief"
    )
    parser.add_argument(
        "--products-file",
        type=str,
        default=None,
        help="Path to JSON file containing products list"
    )
    
    args = parser.parse_args()
    
    # Load brief from file if provided
    brief = None
    if args.brief_file:
        with open(args.brief_file, "r") as f:
            brief_data = json.load(f)
            brief = CreativeBrief(**brief_data)
    
    # Load products from file if provided
    products = None
    if args.products_file:
        with open(args.products_file, "r") as f:
            products = json.load(f)
    
    # Generate content
    try:
        result = await generate_content_sample(
            brief=brief,
            products=products,
            generate_images=not args.no_images,
            output_path=args.output
        )
        
        print(f"\n{'='*70}")
        print("✅ Content generation completed!")
        print(f"{'='*70}\n")
        
        sys.exit(0)
        
    except Exception as e:
        print(f"\n❌ Error during content generation: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


# Example: Custom brief and products
async def custom_example():
    """Example with custom brief and products."""
    
    # Custom brief for a summer promotion
    brief = CreativeBrief(
        overview="Summer outdoor living promotion for patio furniture",
        objectives="Increase summer patio sales by 30%, drive foot traffic to showrooms",
        target_audience="Suburban homeowners, 35-60, with outdoor entertaining spaces",
        key_message="Create your perfect outdoor oasis with our premium patio collection",
        tone_and_style="Relaxed, aspirational, lifestyle-focused. Evoke summer gatherings and outdoor relaxation",
        deliverable="Email banner and 2 social media posts",
        timelines="Launch Memorial Day weekend",
        visual_guidelines="Outdoor settings at golden hour, families enjoying patios, lush greenery, modern outdoor furniture",
        cta="Explore the Summer Collection - 20% off this weekend only"
    )
    
    # Custom products
    products = [
        {
            "id": "patio-1",
            "product_name": "Sunset Lounger",
            "description": "Premium outdoor chaise lounge with weather-resistant cushions in coastal blue",
            "tags": "patio, lounge, outdoor, blue, relaxation",
            "price": 599.99
        },
        {
            "id": "patio-2",
            "product_name": "Garden Dining Set",
            "description": "6-piece aluminum dining set with tempered glass table, perfect for outdoor entertaining",
            "tags": "patio, dining, aluminum, entertaining, family",
            "price": 1299.99
        }
    ]
    
    results = await generate_content_sample(
        brief=brief,
        products=products,
        generate_images=True,
        output_path="custom_content_results.json"
    )
    
    return results


if __name__ == "__main__":
    # Run the main function
    asyncio.run(main())
    
    # Uncomment below to run custom example instead:
    # asyncio.run(custom_example())
