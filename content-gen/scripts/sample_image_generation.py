#!/usr/bin/env python3
"""
Sample Image Generation Script

This script demonstrates how to generate marketing images using the
content-gen image generation capabilities (DALL-E 3 or gpt-image-1).

Prerequisites:
1. Set up environment variables (or use a .env file):
   - AZURE_OPENAI_ENDPOINT: Your Azure OpenAI endpoint
   - AZURE_OPENAI_DALLE_ENDPOINT: (Optional) Dedicated DALL-E endpoint
   - AZURE_OPENAI_DALLE_MODEL: Model name (default: dall-e-3)
   - AZURE_OPENAI_IMAGE_MODEL: (Optional) Use "gpt-image-1" for GPT Image model
   
2. Ensure you have RBAC access:
   - "Cognitive Services OpenAI User" role on the Azure OpenAI resource

Usage:
    python sample_image_generation.py
    python sample_image_generation.py --prompt "A modern kitchen with stainless steel appliances"
    python sample_image_generation.py --size 1024x1792 --quality hd
"""

import asyncio
import argparse
import base64
import os
import sys
from datetime import datetime
from pathlib import Path

# Add the backend directory to the path
backend_path = Path(__file__).parent.parent / "src" / "backend"
sys.path.insert(0, str(backend_path))

# Now import the image generation function
from agents.image_content_agent import generate_dalle_image
from settings import app_settings


async def generate_sample_image(
    prompt: str,
    product_description: str = "",
    scene_description: str = "",
    size: str = None,
    quality: str = None,
    output_path: str = None
) -> dict:
    """
    Generate a sample marketing image.
    
    Args:
        prompt: The main image generation prompt
        product_description: Optional product context for the image
        scene_description: Optional scene/setting description
        size: Image size (default from settings)
        quality: Image quality (default from settings)
        output_path: Path to save the generated image (optional)
    
    Returns:
        Dictionary with generation results
    """
    print(f"\n{'='*60}")
    print("IMAGE GENERATION SAMPLE")
    print(f"{'='*60}")
    print(f"\nModel: {app_settings.azure_openai.effective_image_model}")
    print(f"Endpoint: {app_settings.azure_openai.dalle_endpoint or app_settings.azure_openai.endpoint}")
    print(f"Size: {size or app_settings.azure_openai.image_size}")
    print(f"Quality: {quality or app_settings.azure_openai.image_quality}")
    print(f"\nPrompt: {prompt[:200]}{'...' if len(prompt) > 200 else ''}")
    
    if product_description:
        print(f"Product context: {product_description[:100]}...")
    if scene_description:
        print(f"Scene: {scene_description[:100]}...")
    
    print(f"\n{'='*60}")
    print("Generating image...")
    print(f"{'='*60}\n")
    
    # Call the image generation function
    result = await generate_dalle_image(
        prompt=prompt,
        product_description=product_description,
        scene_description=scene_description,
        size=size,
        quality=quality
    )
    
    if result.get("success"):
        print("✅ Image generated successfully!")
        print(f"   Model used: {result.get('model')}")
        
        if result.get("revised_prompt"):
            print(f"   Revised prompt: {result['revised_prompt'][:150]}...")
        
        # Save the image if we have base64 data
        if result.get("image_base64") and output_path:
            # Decode and save the image
            image_data = base64.b64decode(result["image_base64"])
            
            # Ensure output directory exists
            output_dir = os.path.dirname(output_path)
            if output_dir:
                os.makedirs(output_dir, exist_ok=True)
            
            with open(output_path, "wb") as f:
                f.write(image_data)
            
            print(f"   Saved to: {output_path}")
            print(f"   File size: {len(image_data) / 1024:.1f} KB")
        elif result.get("image_base64"):
            # Generate default output path
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            default_path = f"generated_image_{timestamp}.png"
            
            image_data = base64.b64decode(result["image_base64"])
            with open(default_path, "wb") as f:
                f.write(image_data)
            
            print(f"   Saved to: {default_path}")
            print(f"   File size: {len(image_data) / 1024:.1f} KB")
    else:
        print(f"❌ Image generation failed: {result.get('error')}")
    
    return result


async def main():
    """Main entry point for the sample script."""
    parser = argparse.ArgumentParser(
        description="Generate marketing images using DALL-E 3 or gpt-image-1"
    )
    parser.add_argument(
        "--prompt", "-p",
        type=str,
        default="A modern, minimalist living room with comfortable furniture, soft natural lighting, and plants. Professional marketing photography style.",
        help="The image generation prompt"
    )
    parser.add_argument(
        "--product", "-d",
        type=str,
        default="",
        help="Product description for context"
    )
    parser.add_argument(
        "--scene", "-s",
        type=str,
        default="",
        help="Scene/setting description"
    )
    parser.add_argument(
        "--size",
        type=str,
        choices=["1024x1024", "1024x1792", "1792x1024", "1536x1024", "1024x1536"],
        default=None,
        help="Image size (default from settings)"
    )
    parser.add_argument(
        "--quality", "-q",
        type=str,
        choices=["standard", "hd", "low", "medium", "high"],
        default=None,
        help="Image quality (default from settings)"
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        default=None,
        help="Output file path for the generated image"
    )
    
    args = parser.parse_args()
    
    # Check if image generation is enabled
    if not app_settings.azure_openai.image_generation_enabled:
        print("❌ Image generation is not configured.")
        print("   Please set AZURE_OPENAI_DALLE_ENDPOINT or AZURE_OPENAI_ENDPOINT")
        print("   and ensure you have access to a DALL-E 3 or gpt-image-1 model.")
        sys.exit(1)
    
    # Generate the image
    result = await generate_sample_image(
        prompt=args.prompt,
        product_description=args.product,
        scene_description=args.scene,
        size=args.size,
        quality=args.quality,
        output_path=args.output
    )
    
    # Exit with appropriate code
    sys.exit(0 if result.get("success") else 1)


# Example: Generate multiple themed images
async def generate_themed_examples():
    """Generate a set of example marketing images with different themes."""
    
    themes = [
        {
            "name": "Modern Kitchen",
            "prompt": "A sleek modern kitchen with marble countertops, stainless steel appliances, and pendant lighting. Professional real estate photography.",
            "scene": "Bright, airy kitchen in a contemporary home",
        },
        {
            "name": "Outdoor Living",
            "prompt": "A beautiful outdoor patio with comfortable seating, string lights, and a fire pit at sunset. Lifestyle marketing photography.",
            "scene": "Warm evening atmosphere in a backyard setting",
        },
        {
            "name": "Home Office",
            "prompt": "A minimalist home office with a clean desk, ergonomic chair, natural wood accents, and large windows. Professional interior design photography.",
            "scene": "Productive workspace with natural lighting",
        },
    ]
    
    print("\n" + "="*60)
    print("GENERATING THEMED MARKETING IMAGES")
    print("="*60)
    
    results = []
    for i, theme in enumerate(themes, 1):
        print(f"\n[{i}/{len(themes)}] Generating: {theme['name']}")
        
        result = await generate_sample_image(
            prompt=theme["prompt"],
            scene_description=theme["scene"],
            output_path=f"sample_{theme['name'].lower().replace(' ', '_')}.png"
        )
        results.append({"theme": theme["name"], "result": result})
    
    # Summary
    print("\n" + "="*60)
    print("GENERATION SUMMARY")
    print("="*60)
    
    successful = sum(1 for r in results if r["result"].get("success"))
    print(f"\nSuccessfully generated: {successful}/{len(results)} images")
    
    for r in results:
        status = "✅" if r["result"].get("success") else "❌"
        print(f"  {status} {r['theme']}")
    
    return results


if __name__ == "__main__":
    # Run the main function
    asyncio.run(main())
    
    # Uncomment below to run themed examples instead:
    # asyncio.run(generate_themed_examples())
