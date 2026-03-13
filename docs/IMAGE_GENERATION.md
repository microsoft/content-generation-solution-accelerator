# Image Generation (gpt-image-1-mini / gpt-image-1.5)

## Overview

The accelerator supports image generation through Azure OpenAI image models:

- `gpt-image-1-mini`
- `gpt-image-1.5`

Both models are used through `images.generate()` in the backend image agent. The selected model is controlled by `AZURE_OPENAI_IMAGE_MODEL`.

## Current Model Behavior

### Supported Models

| Model | Status | Primary Use |
|-------|--------|-------------|
| `gpt-image-1-mini` | Supported | General marketing image generation |
| `gpt-image-1.5` | Supported | Higher-quality marketing image generation |

### Prompting Strategy

The `ImageContentAgent` builds a single consolidated prompt from:

- Product context (including ingestion-time image descriptions)
- Creative brief visual guidance
- Brand guidelines
- Safety and style constraints

The agent enforces no-text-in-image constraints and color fidelity requirements in the prompt instructions.

## End-to-End Workflow

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Product Image  │────▶│  GPT-5 Vision   │────▶│ Text Description│
│  (Blob Storage) │     │  (Auto-analyze) │     │   (CosmosDB)    │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                                                        │
                                                        ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│ Marketing Image │◀────│ gpt-image-1-mini/1.5 │◀────│ Combined Prompt │
│    (Output)     │     │   (Generate)    │     │ (Desc + Brief)  │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

#### Step 1: Product Image Ingestion

When a product image is uploaded to Blob Storage, ingestion logic can generate a detailed visual description that is later used as image-generation context.

1. Sends the image to GPT-5 Vision
2. Generates a detailed text description including:
   - Product appearance (colors, shapes, materials)
   - Key visual features
   - Composition and positioning
   - Style and aesthetic qualities
3. Stores the description in CosmosDB alongside product metadata

```python
async def generate_image_description(image_url: str) -> str:
    """Generate detailed text description of product image using GPT-5 Vision."""
    response = await openai_client.chat.completions.create(
        model="gpt-5",
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": """Describe this product image in detail for use in marketing image generation.
                        Include: colors, materials, shape, key features, style, and positioning.
                        Be specific enough that an image generator could recreate a similar product."""
                    },
                    {
                        "type": "image_url",
                        "image_url": {"url": image_url}
                    }
                ]
            }
        ],
        max_tokens=500
    )
    return response.choices[0].message.content
```

#### Step 2: Marketing Image Generation

The image generation flow combines product description context with:

- Creative brief visual guidelines
- Brand guidelines (colors, style, composition rules)
- Scene/context requirements

```python
async def generate_marketing_image(
    product: Product,
    creative_brief: CreativeBrief,
    brand_guidelines: BrandGuidelines
) -> dict:
    """Generate marketing image using the configured GPT image model."""
    
    full_prompt = f"""
    Create a professional marketing image for a retail campaign.
    
    PRODUCT (maintain accuracy):
    {product.image_description}
    
    SCENE:
    {creative_brief.visual_guidelines}
    
    BRAND STYLE:
    - Primary color: {brand_guidelines.primary_color}
    - Style: {brand_guidelines.image_style}
    - Composition: Product centered, 30% negative space
    
    REQUIREMENTS:
    - Professional lighting
    - Clean, modern aesthetic
    - Suitable for {creative_brief.deliverable}
    """

    model_name = app_settings.azure_openai.effective_image_model
    size = app_settings.azure_openai.image_size or "1024x1024"
    quality = app_settings.azure_openai.image_quality or "medium"
    
    response = await openai_client.images.generate(
        model=model_name,
        prompt=full_prompt,
        size=size,
        quality=quality,
        n=1,
    )

    return {"image_base64": response.data[0].b64_json}
```

## Configuration

### Required Environment Variables

- `AZURE_OPENAI_ENDPOINT`
- `AZURE_OPENAI_GPT_MODEL`
- `AZURE_OPENAI_IMAGE_MODEL` (`gpt-image-1-mini`, `gpt-image-1.5`, or `none`)
- `AZURE_OPENAI_GPT_IMAGE_ENDPOINT` (optional if same as main endpoint)
- `AZURE_OPENAI_API_VERSION`
- `AZURE_OPENAI_IMAGE_API_VERSION`

### Optional Image Controls

- `AZURE_OPENAI_IMAGE_SIZE` (for example: `1024x1024`, `1536x1024`, `1024x1536`, `auto`)
- `AZURE_OPENAI_IMAGE_QUALITY` (`low`, `medium`, `high`, `auto`)

## API Usage Pattern

The backend image generator calls Azure OpenAI with:

- `images.generate()`
- `model` set from `AZURE_OPENAI_IMAGE_MODEL`
- prompt text assembled from brief + product + brand constraints
- `size` and `quality` from app settings (or request overrides)

## Limitations of the Workaround

### Accuracy Trade-offs

1. **Product Representation**: The generated product in the marketing image may not be an exact match to the original product. The image model interprets the text description and creates its own version.

2. **Brand-Specific Details**: Logos, specific patterns, or unique design elements may not be accurately reproduced.

3. **Color Matching**: While we include color descriptions, exact color matching is not guaranteed.

### Recommended Use Cases

| Use Case | Suitability |
|----------|-------------|
| Lifestyle/contextual marketing images | ✅ Excellent |
| Social media campaign visuals | ✅ Excellent |
| Concept mockups | ✅ Good |
| Product-in-scene compositions | ✅ Good |
| Exact product photography replacement | ❌ Not recommended |
| Catalog/technical images | ❌ Not recommended |


### Model Availability Notes

1. Deploy either `gpt-image-1-mini` or `gpt-image-1.5` based on quota and regional availability.
2. Set `AZURE_OPENAI_IMAGE_MODEL` to the deployed model name.
3. If using a separate image endpoint, set `AZURE_OPENAI_GPT_IMAGE_ENDPOINT`.
4. Keep `AZURE_OPENAI_IMAGE_API_VERSION` aligned with the image model API version required by your deployment.

## Best Practices

### Optimizing Product Descriptions

For best results with the text-based workaround:

1. **Be Specific**: Include exact colors, materials, and dimensions
2. **Describe Unique Features**: Highlight what makes the product distinctive
3. **Include Context**: Mention typical use cases or settings
4. **Avoid Ambiguity**: Use precise terminology

### Example High-Quality Description

```
A sleek wireless Bluetooth headphone in matte black finish with 
rose gold accents on the ear cup rims and headband adjustment 
sliders. Over-ear cushions in premium memory foam covered with 
soft protein leather. The headband features a padded top section 
with subtle brand embossing. The left ear cup has touch-sensitive 
controls visible as a circular touch pad. Cable port and power 
button are positioned on the bottom edge of the right ear cup. 
Overall aesthetic is premium, modern, and minimalist.
```

## Compliance Considerations

All generated images are validated by the `ComplianceAgent` for:

- Brand color adherence
- Prohibited visual elements
- Appropriate imagery for target audience
- Required disclaimers (added as text overlay if needed)

Images with compliance violations are flagged with appropriate severity levels before user review.
