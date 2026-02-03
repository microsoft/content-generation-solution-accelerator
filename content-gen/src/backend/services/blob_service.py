"""
Blob Storage Service - Manages product images and generated content.

Provides async operations for:
- Product image upload and retrieval
- Generated image storage
- Image description generation via GPT-5 Vision
"""

import base64
import logging
from typing import Optional, Tuple
from datetime import datetime, timezone

from azure.storage.blob.aio import BlobServiceClient, ContainerClient
from azure.identity.aio import DefaultAzureCredential, ManagedIdentityCredential
from openai import AsyncAzureOpenAI

from settings import app_settings

logger = logging.getLogger(__name__)


class BlobStorageService:
    """Service for interacting with Azure Blob Storage."""
    
    def __init__(self):
        self._client: Optional[BlobServiceClient] = None
        self._product_images_container: Optional[ContainerClient] = None
        self._generated_images_container: Optional[ContainerClient] = None
    
    async def _get_credential(self):
        """Get Azure credential for authentication."""
        client_id = app_settings.base_settings.azure_client_id
        if client_id:
            return ManagedIdentityCredential(client_id=client_id)
        return DefaultAzureCredential()
    
    async def initialize(self) -> None:
        """Initialize Blob Storage client and containers."""
        if self._client:
            return
        
        credential = await self._get_credential()
        
        self._client = BlobServiceClient(
            account_url=f"https://{app_settings.blob.account_name}.blob.core.windows.net",
            credential=credential
        )
        
        self._product_images_container = self._client.get_container_client(
            app_settings.blob.product_images_container
        )
        
        self._generated_images_container = self._client.get_container_client(
            app_settings.blob.generated_images_container
        )
        
        logger.info("Blob Storage service initialized")
    
    async def close(self) -> None:
        """Close the Blob Storage client."""
        if self._client:
            await self._client.close()
            self._client = None
    
    # ==================== Product Image Operations ====================
    
    async def upload_product_image(
        self,
        sku: str,
        image_data: bytes,
        content_type: str = "image/jpeg"
    ) -> Tuple[str, str]:
        """
        Upload a product image and generate its description.
        
        Args:
            sku: Product SKU (used as blob name prefix)
            image_data: Raw image bytes
            content_type: MIME type of the image
        
        Returns:
            Tuple of (blob_url, generated_description)
        """
        await self.initialize()
        
        # Generate unique blob name
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        extension = content_type.split("/")[-1]
        blob_name = f"{sku}/{timestamp}.{extension}"
        
        # Upload the image
        blob_client = self._product_images_container.get_blob_client(blob_name)
        await blob_client.upload_blob(
            image_data,
            content_type=content_type,
            overwrite=True
        )
        
        blob_url = blob_client.url
        
        # Generate description using GPT-5 Vision
        description = await self.generate_image_description(image_data)
        
        logger.info(f"Uploaded product image: {blob_name}")
        return blob_url, description
    
    async def get_product_image_url(self, sku: str) -> Optional[str]:
        """
        Get the URL of the latest product image.
        
        Args:
            sku: Product SKU
        
        Returns:
            URL of the latest image, or None if not found
        """
        await self.initialize()
        
        # List blobs with the SKU prefix
        blobs = []
        async for blob in self._product_images_container.list_blobs(
            name_starts_with=f"{sku}/"
        ):
            blobs.append(blob)
        
        if not blobs:
            return None
        
        # Get the most recent blob
        latest_blob = sorted(blobs, key=lambda b: b.name, reverse=True)[0]
        blob_client = self._product_images_container.get_blob_client(latest_blob.name)
        
        return blob_client.url
    
    # ==================== Generated Image Operations ====================
    
    async def save_generated_image(
        self,
        conversation_id: str,
        image_base64: str,
        content_type: str = "image/png"
    ) -> str:
        """
        Save a DALL-E generated image to blob storage.
        
        Args:
            conversation_id: ID of the conversation that generated the image
            image_base64: Base64-encoded image data
            content_type: MIME type of the image
        
        Returns:
            URL of the saved image
        """
        await self.initialize()
        
        # Decode base64 image
        image_data = base64.b64decode(image_base64)
        
        # Generate unique blob name
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        extension = content_type.split("/")[-1]
        blob_name = f"{conversation_id}/{timestamp}.{extension}"
        
        # Upload the image
        blob_client = self._generated_images_container.get_blob_client(blob_name)
        await blob_client.upload_blob(
            image_data,
            content_type=content_type,
            overwrite=True
        )
        
        logger.info(f"Saved generated image: {blob_name}")
        return blob_client.url
    
    async def get_generated_images(
        self,
        conversation_id: str
    ) -> list[str]:
        """
        Get all generated images for a conversation.
        
        Args:
            conversation_id: ID of the conversation
        
        Returns:
            List of image URLs
        """
        await self.initialize()
        
        urls = []
        async for blob in self._generated_images_container.list_blobs(
            name_starts_with=f"{conversation_id}/"
        ):
            blob_client = self._generated_images_container.get_blob_client(blob.name)
            urls.append(blob_client.url)
        
        return urls
    
    # ==================== Image Description Generation ====================
    
    async def generate_image_description(self, image_data: bytes) -> str:
        """
        Generate a detailed text description of an image using GPT-5 Vision.
        
        This is used to create descriptions of product images that can be
        used as context for DALL-E 3 image generation (since DALL-E 3
        cannot accept image inputs directly).
        
        Args:
            image_data: Raw image bytes
        
        Returns:
            Detailed text description of the image
        """
        # Encode image to base64
        image_base64 = base64.b64encode(image_data).decode("utf-8")
        
        try:
            credential = await self._get_credential()
            token = await credential.get_token("https://cognitiveservices.azure.com/.default")
            
            client = AsyncAzureOpenAI(
                azure_endpoint=app_settings.azure_openai.endpoint,
                azure_ad_token=token.token,
                api_version=app_settings.azure_openai.api_version,
            )
            
            response = await client.chat.completions.create(
                model=app_settings.azure_openai.gpt_model,
                messages=[
                    {
                        "role": "system",
                        "content": """You are an expert at describing product images for marketing purposes.
Provide detailed, accurate descriptions that capture:
- Product appearance (shape, color, materials, finish)
- Key visual features and design elements
- Size and proportions (relative descriptions)
- Styling and aesthetic qualities
- Any visible branding or labels

Your descriptions will be used to guide AI image generation, so be specific and vivid."""
                    },
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "Describe this product image in detail for use in marketing content generation:"
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{image_base64}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=500
            )
            
            description = response.choices[0].message.content
            logger.info(f"Generated image description: {description[:100]}...")
            return description
            
        except Exception as e:
            logger.exception(f"Error generating image description: {e}")
            return "Product image - description unavailable"


# Singleton instance
_blob_service: Optional[BlobStorageService] = None


async def get_blob_service() -> BlobStorageService:
    """Get or create the singleton Blob Storage service instance."""
    global _blob_service
    if _blob_service is None:
        _blob_service = BlobStorageService()
        await _blob_service.initialize()
    return _blob_service
