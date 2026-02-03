"""Image Content Agent - Generates marketing images via DALL-E 3, gpt-image-1, or gpt-image-1.5.

Provides the generate_image function used by the orchestrator
to create marketing images using either DALL-E 3, gpt-image-1, or gpt-image-1.5.
"""

import logging

from openai import AsyncAzureOpenAI
from azure.identity.aio import DefaultAzureCredential, ManagedIdentityCredential

from settings import app_settings

logger = logging.getLogger(__name__)


def _truncate_for_dalle(product_description: str, max_chars: int = 1500) -> str:
    """
    Truncate product descriptions to fit DALL-E's 4000 character limit.
    Extracts the most visually relevant information (colors, hex codes, finishes).
    
    Args:
        product_description: The full product description(s)
        max_chars: Maximum characters to allow for product context
        
    Returns:
        Truncated description with essential visual details
    """
    if not product_description or len(product_description) <= max_chars:
        return product_description
    
    import re
    
    # Extract essential visual info: product names, hex codes, color descriptions
    lines = product_description.split('\n')
    essential_parts = []
    current_product = ""
    
    for line in lines:
        # Keep product name headers
        if line.startswith('### '):
            current_product = line
            essential_parts.append(line)
        # Keep hex code references
        elif 'hex' in line.lower() or '#' in line:
            if current_product and current_product not in essential_parts[-5:]:
                essential_parts.append(current_product)
            essential_parts.append(line.strip())
        # Keep first sentence of description (usually has the main color)
        elif line.strip().startswith('"') and 'appears as' in line.lower():
            # Extract first two sentences
            sentences = re.split(r'(?<=[.!?])\s+', line.strip())
            essential_parts.append(' '.join(sentences[:2]))
        # Keep finish descriptions
        elif 'finish' in line.lower() or 'matte' in line.lower() or 'eggshell' in line.lower():
            essential_parts.append(line.strip()[:200])
    
    result = '\n'.join(essential_parts)
    
    # If still too long, just truncate with ellipsis
    if len(result) > max_chars:
        result = result[:max_chars-50] + '\n\n[Additional details truncated for DALL-E]'
    
    return result


async def generate_dalle_image(
    prompt: str,
    product_description: str = "",
    scene_description: str = "",
    size: str = None,
    quality: str = None
) -> dict:
    """
    Generate a marketing image using DALL-E 3, gpt-image-1, or gpt-image-1.5.
    
    The model used is determined by AZURE_OPENAI_IMAGE_MODEL setting.
    
    Args:
        prompt: The main image generation prompt
        product_description: Auto-generated description of product image (for context)
        scene_description: Scene/setting description from creative brief
        size: Image size (model-specific, uses settings default if not provided)
              - dall-e-3: 1024x1024, 1024x1792, 1792x1024
              - gpt-image-1/1.5: 1024x1024, 1536x1024, 1024x1536, auto
        quality: Image quality (model-specific, uses settings default if not provided)
              - dall-e-3: standard, hd
              - gpt-image-1/1.5: low, medium, high, auto
    
    Returns:
        Dictionary containing generated image data and metadata
    """
    # Determine which model to use
    image_model = app_settings.azure_openai.effective_image_model
    logger.info(f"Using image generation model: {image_model}")
    
    # Use appropriate generator based on model
    if image_model in ["gpt-image-1", "gpt-image-1.5"]:
        return await _generate_gpt_image(prompt, product_description, scene_description, size, quality)
    else:
        return await _generate_dalle_image(prompt, product_description, scene_description, size, quality)


async def _generate_dalle_image(
    prompt: str,
    product_description: str = "",
    scene_description: str = "",
    size: str = None,
    quality: str = None
) -> dict:
    """
    Generate a marketing image using DALL-E 3.
    
    Args:
        prompt: The main image generation prompt
        product_description: Auto-generated description of product image (for context)
        scene_description: Scene/setting description from creative brief
        size: Image size (1024x1024, 1024x1792, 1792x1024)
        quality: Image quality (standard, hd)
    
    Returns:
        Dictionary containing generated image data and metadata
    """
    brand = app_settings.brand_guidelines
    
    # Use defaults from settings if not provided
    size = size or app_settings.azure_openai.image_size
    quality = quality or app_settings.azure_openai.image_quality
    
    # DALL-E 3 has a 4000 character limit for prompts
    # Truncate product descriptions to essential visual info
    truncated_product_desc = _truncate_for_dalle(product_description, max_chars=1500)
    
    # Also truncate the main prompt if it's too long
    main_prompt = prompt[:1000] if len(prompt) > 1000 else prompt
    scene_desc = scene_description[:500] if scene_description and len(scene_description) > 500 else scene_description
    
    # Build the full prompt with product context and brand guidelines
    full_prompt = f"""⚠️ ABSOLUTE RULE: THIS IMAGE MUST CONTAIN ZERO TEXT. NO WORDS. NO LETTERS. NO PRODUCT NAMES. NO LABELS.

Create a professional marketing image that is PURELY VISUAL with absolutely no text, typography, words, letters, numbers, or written content of any kind.

{brand.get_image_generation_prompt()}

PRODUCT CONTEXT:
{truncated_product_desc if truncated_product_desc else 'No specific product - create a lifestyle/brand image'}

SCENE:
{scene_desc if scene_desc else main_prompt}

MAIN REQUIREMENT:
{main_prompt}

MANDATORY FINAL CHECKLIST:
✗ NO product names in the image
✗ NO color names in the image  
✗ NO text overlays or labels
✗ NO typography or lettering of any kind
✗ NO watermarks or logos
✗ NO signage or captions
✓ ONLY visual elements - colors, textures, products, scenes
✓ Accurately reproduce product colors using exact hex codes
✓ Professional, polished marketing image
"""
    
    # Final safety check - DALL-E 3 has 4000 char limit
    if len(full_prompt) > 3900:
        logger.warning(f"Prompt too long ({len(full_prompt)} chars), truncating...")
        # Reduce product context further
        truncated_product_desc = _truncate_for_dalle(product_description, max_chars=800)
        full_prompt = f"""⚠️ ZERO TEXT IN IMAGE. NO WORDS. NO LETTERS. NO PRODUCT NAMES.

Create a PURELY VISUAL marketing image with no text whatsoever.

PRODUCT: {truncated_product_desc[:600] if truncated_product_desc else 'Lifestyle/brand image'}

SCENE: {scene_desc[:300] if scene_desc else main_prompt[:300]}

REQUIREMENT: {main_prompt[:500]}

Style: Modern, clean, minimalist. Brand colors: {brand.primary_color}, {brand.secondary_color}. High visual impact.

⚠️ FINAL CHECK: NO text, NO product names, NO color names, NO labels, NO typography. Image must be 100% text-free.
"""

    try:
        # Get credential
        client_id = app_settings.base_settings.azure_client_id
        if client_id:
            credential = ManagedIdentityCredential(client_id=client_id)
        else:
            credential = DefaultAzureCredential()
        
        # Get token for Azure OpenAI
        token = await credential.get_token("https://cognitiveservices.azure.com/.default")
        
        # Use the dedicated DALL-E endpoint if configured, otherwise fall back to main endpoint
        dalle_endpoint = app_settings.azure_openai.dalle_endpoint or app_settings.azure_openai.endpoint
        logger.info(f"Using DALL-E endpoint: {dalle_endpoint}")
        
        client = AsyncAzureOpenAI(
            azure_endpoint=dalle_endpoint,
            azure_ad_token=token.token,
            api_version=app_settings.azure_openai.preview_api_version,
        )
        
        try:
            response = await client.images.generate(
                model=app_settings.azure_openai.dalle_model,
                prompt=full_prompt,
                size=size,
                quality=quality,
                n=1,
                response_format="b64_json"
            )
            
            image_data = response.data[0]
            
            return {
                "success": True,
                "image_base64": image_data.b64_json,
                "prompt_used": full_prompt,
                "revised_prompt": getattr(image_data, 'revised_prompt', None),
                "model": "dall-e-3",
            }
        finally:
            # Properly close the async client to avoid unclosed session warnings
            await client.close()
        
    except Exception as e:
        logger.exception(f"Error generating DALL-E image: {e}")
        return {
            "success": False,
            "error": str(e),
            "prompt_used": full_prompt,
            "model": "dall-e-3",
        }


async def _generate_gpt_image(
    prompt: str,
    product_description: str = "",
    scene_description: str = "",
    size: str = None,
    quality: str = None
) -> dict:
    """
    Generate a marketing image using gpt-image-1 or gpt-image-1.5.
    
    gpt-image models have different capabilities than DALL-E 3:
    - Supports larger prompt sizes
    - Different size options: 1024x1024, 1536x1024, 1024x1536, auto
    - Different quality options: low, medium, high, auto
    - May have better instruction following
    
    Args:
        prompt: The main image generation prompt
        product_description: Auto-generated description of product image (for context)
        scene_description: Scene/setting description from creative brief
        size: Image size (1024x1024, 1536x1024, 1024x1536, auto)
        quality: Image quality (low, medium, high, auto)
    
    Returns:
        Dictionary containing generated image data and metadata
    """
    brand = app_settings.brand_guidelines
    
    # Use defaults from settings if not provided
    # Map DALL-E quality settings to gpt-image-1 or gpt-image-1.5 equivalents if needed
    size = size or app_settings.azure_openai.image_size
    quality = quality or app_settings.azure_openai.image_quality
    
    # Map DALL-E quality values to gpt-image-1 or gpt-image-1.5 equivalents
    quality_mapping = {
        "standard": "medium",
        "hd": "high",
    }
    quality = quality_mapping.get(quality, quality)
    
    # Map DALL-E sizes to gpt-image-1 or gpt-image-1.5 equivalents if needed
    size_mapping = {
        "1024x1792": "1024x1536",  # Closest equivalent
        "1792x1024": "1536x1024",  # Closest equivalent
    }
    size = size_mapping.get(size, size)
    
    # gpt-image-1 can handle larger prompts, so we can include more context
    truncated_product_desc = _truncate_for_dalle(product_description, max_chars=3000)
    
    main_prompt = prompt[:2000] if len(prompt) > 2000 else prompt
    scene_desc = scene_description[:1000] if scene_description and len(scene_description) > 1000 else scene_description
    
    # Build the full prompt with product context and brand guidelines
    full_prompt = f"""⚠️ ABSOLUTE RULE: THIS IMAGE MUST CONTAIN ZERO TEXT. NO WORDS. NO LETTERS. NO PRODUCT NAMES. NO COLOR NAMES. NO LABELS.

Create a professional marketing image for retail advertising that is PURELY VISUAL with absolutely no text, typography, words, letters, numbers, or written content of any kind.

{brand.get_image_generation_prompt()}

PRODUCT CONTEXT:
{truncated_product_desc if truncated_product_desc else 'No specific product - create a lifestyle/brand image'}

SCENE DESCRIPTION:
{scene_desc if scene_desc else main_prompt}

MAIN REQUIREMENT:
{main_prompt}

MANDATORY FINAL CHECKLIST:
✗ NO product names anywhere in the image (not "Snow Veil", not "Cloud Drift", etc.)
✗ NO color names in the image (not "white", "blue", "gray", etc.)
✗ NO text overlays, labels, or captions
✗ NO typography or lettering of any kind
✗ NO watermarks, logos, or brand names
✗ NO signage or written content
✓ ONLY visual elements - paint swatches, textures, products, lifestyle scenes
✓ Accurately reproduce product colors using exact hex codes
✓ Professional, polished marketing image with brand colors: {brand.primary_color}, {brand.secondary_color}
✓ Modern, aspirational aesthetic with bright, optimistic lighting
"""

    try:
        # Get credential
        client_id = app_settings.base_settings.azure_client_id
        if client_id:
            credential = ManagedIdentityCredential(client_id=client_id)
        else:
            credential = DefaultAzureCredential()
        
        # Get token for Azure OpenAI
        token = await credential.get_token("https://cognitiveservices.azure.com/.default")
        
        # Use gpt-image-1 specific endpoint if configured, otherwise DALL-E endpoint, otherwise main endpoint
        image_endpoint = (
            app_settings.azure_openai.gpt_image_endpoint or 
            app_settings.azure_openai.dalle_endpoint or 
            app_settings.azure_openai.endpoint
        )
        logger.info(f"Using gpt-image-1 endpoint: {image_endpoint}")
        
        # Use the image-specific API version for gpt-image-1 (requires 2025-04-01-preview or newer)
        client = AsyncAzureOpenAI(
            azure_endpoint=image_endpoint,
            azure_ad_token=token.token,
            api_version=app_settings.azure_openai.image_api_version,
        )
        
        try:
            # gpt-image-1/1.5 API call - note: gpt-image doesn't support response_format parameter
            # It returns base64 data directly in the response
            response = await client.images.generate(
                model=app_settings.azure_openai.effective_image_model,
                prompt=full_prompt,
                size=size,
                quality=quality,
                n=1,
            )
            
            image_data = response.data[0]
            
            # gpt-image-1 returns b64_json directly without needing response_format parameter
            image_base64 = getattr(image_data, 'b64_json', None)
            
            # If no b64_json, try to get URL and fetch the image
            if not image_base64 and hasattr(image_data, 'url') and image_data.url:
                import aiohttp
                async with aiohttp.ClientSession() as session:
                    async with session.get(image_data.url) as resp:
                        if resp.status == 200:
                            import base64
                            image_bytes = await resp.read()
                            image_base64 = base64.b64encode(image_bytes).decode('utf-8')
            
            if not image_base64:
                return {
                    "success": False,
                    "error": "No image data returned from gpt-image-1",
                    "prompt_used": full_prompt,
                    "model": "gpt-image-1",
                }
            
            return {
                "success": True,
                "image_base64": image_base64,
                "prompt_used": full_prompt,
                "revised_prompt": getattr(image_data, 'revised_prompt', None),
                "model": "gpt-image-1",
            }
        finally:
            # Properly close the async client to avoid unclosed session warnings
            await client.close()
        
    except Exception as e:
        logger.exception(f"Error generating gpt-image-1 image: {e}")
        return {
            "success": False,
            "error": str(e),
            "prompt_used": full_prompt,
            "model": "gpt-image-1",
        }


# Alias for backwards compatibility
generate_image = generate_dalle_image
