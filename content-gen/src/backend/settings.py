"""
Application settings for the Intelligent Content Generation Accelerator.

Uses Pydantic settings management with environment variable configuration.
Includes brand guidelines as solution parameters for content strategy
and compliance validation.
"""

import os
from typing import List, Optional

from pydantic import BaseModel, Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing_extensions import Self

DOTENV_PATH = os.environ.get(
    "DOTENV_PATH", os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env")
)


def parse_comma_separated(value: str) -> List[str]:
    """Parse a comma-separated string into a list."""
    if isinstance(value, str) and len(value) > 0:
        return [item.strip() for item in value.split(",") if item.strip()]
    return []


class _UiSettings(BaseSettings):
    """UI configuration settings."""
    model_config = SettingsConfigDict(
        env_prefix="UI_", env_file=DOTENV_PATH, extra="ignore", env_ignore_empty=True
    )

    app_name: str = "Content Generation Accelerator"


class _ChatHistorySettings(BaseSettings):
    """CosmosDB chat history configuration."""
    model_config = SettingsConfigDict(
        env_prefix="AZURE_COSMOSDB_",
        env_file=DOTENV_PATH,
        extra="ignore",
        env_ignore_empty=True,
    )

    database: str
    account: str
    account_key: Optional[str] = None
    conversations_container: str
    products_container: str = "products"
    enable_feedback: bool = True


class _AzureOpenAISettings(BaseSettings):
    """Azure OpenAI configuration for GPT and image generation models."""
    model_config = SettingsConfigDict(
        env_prefix="AZURE_OPENAI_",
        env_file=DOTENV_PATH,
        extra="ignore",
        env_ignore_empty=True,
    )

    gpt_model: str = Field(default="gpt-5", alias="AZURE_OPENAI_GPT_MODEL")
    model: str = "gpt-5"
    
    # Image generation model settings
    # Supported models: "dall-e-3" or "gpt-image-1" or "gpt-image-1.5"
    image_model: str = Field(default="dall-e-3", alias="AZURE_OPENAI_IMAGE_MODEL")
    dalle_model: str = Field(default="dall-e-3", alias="AZURE_OPENAI_DALLE_MODEL")  # Legacy alias
    dalle_endpoint: Optional[str] = Field(default=None, alias="AZURE_OPENAI_DALLE_ENDPOINT")
    
    # gpt-image-1 or gpt-image-1.5 specific endpoint (if different from DALL-E endpoint)
    gpt_image_endpoint: Optional[str] = Field(default=None, alias="AZURE_OPENAI_GPT_IMAGE_ENDPOINT")
    
    resource: Optional[str] = None
    endpoint: Optional[str] = None
    temperature: float = 0.7
    top_p: float = 0.95
    max_tokens: int = 2000
    stream: bool = True
    api_version: str = "2024-06-01"
    preview_api_version: str = "2024-02-01"
    image_api_version: str = Field(default="2025-04-01-preview", alias="AZURE_OPENAI_IMAGE_API_VERSION")
    
    # Image generation settings
    # For dall-e-3: 1024x1024, 1024x1792, 1792x1024
    # For gpt-image-1: 1024x1024, 1536x1024, 1024x1536, auto
    image_size: str = "1024x1024"
    image_quality: str = "hd"  # dall-e-3: standard/hd, gpt-image-1: low/medium/high/auto
    
    @property
    def effective_image_model(self) -> str:
        """Get the effective image model, preferring image_model over dalle_model."""
        # If image_model is explicitly set and not the default, use it
        # Otherwise fall back to dalle_model for backwards compatibility
        return self.image_model if self.image_model else self.dalle_model
    
    @property
    def image_endpoint(self) -> Optional[str]:
        """Get the appropriate endpoint for the configured image model."""
        if self.effective_image_model in ["gpt-image-1", "gpt-image-1.5"] and self.gpt_image_endpoint:
            return self.gpt_image_endpoint
        return self.dalle_endpoint

    @property
    def image_generation_enabled(self) -> bool:
        """Check if image generation is available.
        
        Image generation requires either:
        - A DALL-E endpoint configured, OR
        - A gpt-image-1 or gpt-image-1.5 endpoint configured, OR
        - Using the main OpenAI endpoint with an image model configured
        
        Returns False if image_model is explicitly set to empty string or "none".
        """
        # Check if image generation is explicitly disabled
        if not self.image_model or self.image_model.lower() in ("none", "disabled", ""):
            return False
        
        # Check if we have an endpoint that can handle image generation
        # Either a dedicated image endpoint or the main OpenAI endpoint
        has_image_endpoint = bool(self.dalle_endpoint or self.gpt_image_endpoint or self.endpoint)
        
        return has_image_endpoint

    @model_validator(mode="after")
    def ensure_endpoint(self) -> Self:
        if self.endpoint:
            return self
        elif self.resource:
            self.endpoint = f"https://{self.resource}.openai.azure.com"
            return self
        raise ValueError("AZURE_OPENAI_ENDPOINT or AZURE_OPENAI_RESOURCE is required")


class _StorageSettings(BaseSettings):
    """Azure Blob Storage configuration."""
    model_config = SettingsConfigDict(
        env_prefix="AZURE_BLOB_",
        env_file=DOTENV_PATH,
        extra="ignore",
        env_ignore_empty=True,
    )

    account_name: str = Field(default="", alias="AZURE_BLOB_ACCOUNT_NAME")
    product_images_container: str = "product-images"
    generated_images_container: str = "generated-images"


class _CosmosSettings(BaseSettings):
    """Azure Cosmos DB configuration."""
    model_config = SettingsConfigDict(
        env_prefix="AZURE_COSMOS_",
        env_file=DOTENV_PATH,
        extra="ignore",
        env_ignore_empty=True,
    )

    endpoint: str = Field(default="", alias="AZURE_COSMOS_ENDPOINT")
    database_name: str = Field(default="content-generation", alias="AZURE_COSMOS_DATABASE_NAME")
    products_container: str = "products"
    conversations_container: str = "conversations"


class _AIFoundrySettings(BaseSettings):
    """Azure AI Foundry configuration for agent-based workflows.
    
    When USE_FOUNDRY=true, the orchestrator uses Azure AI Foundry's
    project endpoint instead of direct Azure OpenAI endpoints.
    """
    model_config = SettingsConfigDict(
        env_file=DOTENV_PATH,
        extra="ignore",
        env_ignore_empty=True,
    )

    use_foundry: bool = Field(default=False, alias="USE_FOUNDRY")
    project_endpoint: Optional[str] = Field(default=None, alias="AZURE_AI_PROJECT_ENDPOINT")
    project_name: Optional[str] = Field(default=None, alias="AZURE_AI_PROJECT_NAME")
    
    # Model deployment names in Foundry
    model_deployment: Optional[str] = Field(default=None, alias="AZURE_AI_MODEL_DEPLOYMENT_NAME")
    image_deployment: str = Field(default="gpt-image-1", alias="AZURE_AI_IMAGE_MODEL_DEPLOYMENT")


class _SearchSettings(BaseSettings):
    """Azure AI Search configuration."""
    model_config = SettingsConfigDict(
        env_prefix="AZURE_AI_SEARCH_",
        env_file=DOTENV_PATH,
        extra="ignore",
        env_ignore_empty=True,
    )

    endpoint: str = Field(default="", alias="AZURE_AI_SEARCH_ENDPOINT")
    products_index: str = Field(default="products", alias="AZURE_AI_SEARCH_PRODUCTS_INDEX")
    images_index: str = Field(default="product-images", alias="AZURE_AI_SEARCH_IMAGE_INDEX")
    admin_key: Optional[str] = Field(default=None, alias="AZURE_AI_SEARCH_ADMIN_KEY")


class _BrandGuidelinesSettings(BaseSettings):
    """
    Brand guidelines stored as solution parameters.
    
    These are injected into all agent instructions for content strategy
    and compliance validation.
    """
    model_config = SettingsConfigDict(
        env_prefix="BRAND_",
        env_file=DOTENV_PATH,
        extra="ignore",
        env_ignore_empty=True,
    )

    # Voice and tone
    tone: str = "Professional yet approachable"
    voice: str = "Innovative, trustworthy, customer-focused"
    
    # Content restrictions (stored as comma-separated strings)
    prohibited_words_str: str = Field(default="", alias="BRAND_PROHIBITED_WORDS")
    required_disclosures_str: str = Field(default="", alias="BRAND_REQUIRED_DISCLOSURES")
    
    # Visual guidelines
    primary_color: str = "#0078D4"
    secondary_color: str = "#107C10"
    image_style: str = "Modern, clean, minimalist with bright lighting"
    typography: str = "Sans-serif, bold headlines, readable body text"
    
    # Compliance rules
    max_headline_length: int = 60
    max_body_length: int = 500
    require_cta: bool = True
    
    @property
    def prohibited_words(self) -> List[str]:
        """Parse prohibited words from comma-separated string."""
        return parse_comma_separated(self.prohibited_words_str)
    
    @property
    def required_disclosures(self) -> List[str]:
        """Parse required disclosures from comma-separated string."""
        return parse_comma_separated(self.required_disclosures_str)
    
    def get_compliance_prompt(self) -> str:
        """Generate compliance rules text for agent instructions."""
        return f"""
## Brand Compliance Rules

### Voice and Tone
- Tone: {self.tone}
- Voice: {self.voice}

### Content Restrictions
- Prohibited words: {', '.join(self.prohibited_words) if self.prohibited_words else 'None specified'}
- Required disclosures: {', '.join(self.required_disclosures) if self.required_disclosures else 'None required'}
- Maximum headline length: approximately {self.max_headline_length} characters (headline field only)
- Maximum body length: approximately {self.max_body_length} characters (body field only, NOT including headline or tagline)
- CTA required: {'Yes' if self.require_cta else 'No'}

**IMPORTANT: Character Limit Guidelines**
- Character limits apply to INDIVIDUAL fields: headline, body, and tagline are counted SEPARATELY
- The body limit ({self.max_body_length} chars) applies ONLY to the body/description text, not the combined content
- Do NOT flag character limit issues as ERROR - use WARNING severity since exact counting may vary
- When in doubt about length, do NOT flag it as a violation - focus on content quality instead

### Visual Guidelines
- Primary brand color: {self.primary_color}
- Secondary brand color: {self.secondary_color}
- Image style: {self.image_style}
- Typography: {self.typography}

### Compliance Severity Levels
- ERROR: Legal/regulatory violations that MUST be fixed before content can be used
- WARNING: Brand guideline deviations that should be reviewed
- INFO: Style suggestions for improvement (optional)

When validating content, categorize each violation with the appropriate severity level.

## Responsible AI Guidelines

### Content Safety Principles
You MUST follow these Responsible AI principles in ALL generated content:

**Fairness & Inclusion**
- Ensure diverse and inclusive representation in all content
- Avoid stereotypes based on gender, race, age, disability, religion, or background
- Use gender-neutral language when appropriate
- Represent diverse body types, abilities, and backgrounds authentically

**Reliability & Safety**
- Do not generate content that could cause physical, emotional, or financial harm
- Avoid misleading claims, exaggerations, or false promises
- Ensure factual accuracy; do not fabricate statistics or testimonials
- Include appropriate disclaimers for health, financial, or legal topics

**Privacy & Security**
- Never include real personal information (names, addresses, phone numbers)
- Do not reference specific individuals without explicit permission
- Avoid content that could enable identity theft or fraud

**Transparency**
- Be transparent about AI-generated content when required by regulations
- Do not create content designed to deceive or manipulate
- Avoid deepfake-style content or impersonation

**Harmful Content Prevention**
- NEVER generate hateful, discriminatory, or offensive content
- NEVER create violent, graphic, or disturbing imagery
- NEVER produce sexually explicit or suggestive content
- NEVER generate content promoting illegal activities
- NEVER create content that exploits or harms minors

### Image Generation Specific Guidelines
When generating images:
- Do not create realistic images of identifiable real people
- Avoid generating images that could be mistaken for real photographs in misleading contexts
- Ensure generated humans represent diverse demographics positively
- Do not generate images depicting violence, weapons, or harmful activities
- Avoid culturally insensitive or appropriative imagery

**IMPORTANT - Photorealistic Product Images Are ACCEPTABLE:**
Photorealistic style for PRODUCT photography (e.g., paint cans, products, room scenes, textures) 
is our standard marketing style and should NOT be flagged as a violation. Only flag photorealistic 
content when it involves:
- Fake/deepfake identifiable real people (SEVERITY: ERROR)
- Misleading contexts designed to deceive consumers (SEVERITY: ERROR)
Do NOT flag photorealistic product shots, room scenes, or marketing imagery as violations.

### Compliance Validation
The Compliance Agent MUST flag any content that violates these RAI principles as SEVERITY: ERROR.
RAI violations are non-negotiable and content must be regenerated.
"""

    def get_text_generation_prompt(self) -> str:
        """Generate brand guidelines for text content generation."""
        return f"""
## Brand Voice Guidelines

Write content that embodies these characteristics:
- Tone: {self.tone}
- Voice: {self.voice}

### Writing Rules
- Keep headlines under approximately {self.max_headline_length} characters
- Keep body copy (description) under approximately {self.max_body_length} characters
- Note: Character limits are approximate guidelines - focus on concise, impactful writing
- {'Always include a clear call-to-action' if self.require_cta else 'CTA is optional'}
- NEVER use these words: {', '.join(self.prohibited_words) if self.prohibited_words else 'No restrictions'}
- Include these disclosures when applicable: {', '.join(self.required_disclosures) if self.required_disclosures else 'None required'}

## Responsible AI - Text Content Rules

NEVER generate text that:
- Contains hateful, discriminatory, or offensive language
- Makes false claims, fabricated statistics, or fake testimonials
- Includes misleading health, financial, or legal advice
- Uses manipulative or deceptive persuasion tactics
- Promotes illegal activities or harmful behaviors
- Stereotypes any group based on gender, race, age, or background
- Contains sexually explicit or inappropriate content
- Could cause physical, emotional, or financial harm

ALWAYS ensure:
- Factual accuracy and honest representation
- Inclusive language that respects all audiences
- Clear disclaimers where legally required
- Transparency about product limitations
- Respectful portrayal of diverse communities
"""

    def get_image_generation_prompt(self) -> str:
        """Generate brand guidelines for image content generation."""
        return f"""
## ⚠️ MANDATORY: ZERO TEXT IN IMAGE

THE GENERATED IMAGE MUST NOT CONTAIN ANY TEXT WHATSOEVER:
- ❌ NO product names (do not write "Snow Veil", "Cloud Drift", or any paint name)
- ❌ NO color names (do not write "white", "blue", "gray", etc.)
- ❌ NO words, letters, numbers, or typography of any kind
- ❌ NO labels, captions, signage, or watermarks
- ❌ NO logos or brand names
- ✓ ONLY visual elements: paint swatches, color samples, textures, scenes

This is a strict requirement. Text will be added separately by the application.

## Brand Visual Guidelines

Create images that follow these guidelines:
- Style: {self.image_style}
- Primary brand color to incorporate: {self.primary_color}
- Secondary accent color: {self.secondary_color}
- Professional, high-quality imagery suitable for marketing
- Bright, optimistic lighting
- Clean composition with 30% negative space
- No competitor products or logos
- Diverse representation if people are shown

## Color Accuracy

When product colors are specified (especially with hex codes):
- Reproduce the exact colors as accurately as possible
- Use the hex codes as the definitive color reference
- Ensure paint/product colors match the descriptions precisely

## Responsible AI - Image Generation Rules

NEVER generate images that contain:
- Real identifiable people (celebrities, politicians, public figures)
- Violence, weapons, blood, or injury
- Sexually explicit, suggestive, or inappropriate content
- Hateful symbols, slurs, or discriminatory imagery
- Content exploiting or depicting minors inappropriately
- Deepfake-style realistic faces intended to deceive
- Culturally insensitive stereotypes or appropriation
- Illegal activities or substances

ALWAYS ensure:
- Diverse and positive representation of people
- Age-appropriate content suitable for all audiences
- Authentic portrayal without harmful stereotypes
- Clear distinction that this is marketing imagery
- Respect for cultural and religious sensitivities
"""


class _BaseSettings(BaseSettings):
    """Base application settings."""
    model_config = SettingsConfigDict(
        env_file=DOTENV_PATH,
        extra="ignore",
        arbitrary_types_allowed=True,
        env_ignore_empty=True,
    )
    auth_enabled: bool = False
    sanitize_answer: bool = False
    solution_name: Optional[str] = Field(default=None)
    azure_client_id: Optional[str] = Field(default=None, alias="AZURE_CLIENT_ID")


class _AppSettings(BaseModel):
    """Main application settings container."""
    base_settings: _BaseSettings = _BaseSettings()
    azure_openai: _AzureOpenAISettings = _AzureOpenAISettings()
    ai_foundry: _AIFoundrySettings = _AIFoundrySettings()
    brand_guidelines: _BrandGuidelinesSettings = _BrandGuidelinesSettings()
    ui: Optional[_UiSettings] = _UiSettings()
    
    # Constructed properties
    chat_history: Optional[_ChatHistorySettings] = None
    blob: Optional[_StorageSettings] = None
    cosmos: Optional[_CosmosSettings] = None
    search: Optional[_SearchSettings] = None

    @model_validator(mode="after")
    def set_chat_history_settings(self) -> Self:
        try:
            self.chat_history = _ChatHistorySettings()
        except Exception:
            self.chat_history = None
        return self

    @model_validator(mode="after")
    def set_storage_settings(self) -> Self:
        try:
            self.blob = _StorageSettings()
        except Exception:
            self.blob = None
        return self

    @model_validator(mode="after")
    def set_cosmos_settings(self) -> Self:
        try:
            self.cosmos = _CosmosSettings()
        except Exception:
            self.cosmos = None
        return self

    @model_validator(mode="after")
    def set_search_settings(self) -> Self:
        try:
            self.search = _SearchSettings()
        except Exception:
            self.search = None
        return self


# Global settings instance
app_settings = _AppSettings()
