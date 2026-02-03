"""
Azure AI Search Service for grounding content generation.

Provides search capabilities across products and images for
AI content generation grounding.
"""

import logging
from typing import Any, Dict, List, Optional

from azure.core.credentials import AzureKeyCredential
from azure.identity import DefaultAzureCredential
from azure.search.documents import SearchClient

from settings import app_settings

logger = logging.getLogger(__name__)


class SearchService:
    """Service for searching products and images in Azure AI Search."""
    
    def __init__(self):
        self._products_client: Optional[SearchClient] = None
        self._images_client: Optional[SearchClient] = None
        self._credential = None
    
    def _get_credential(self):
        """Get search credential - prefer RBAC, fall back to API key."""
        if self._credential:
            return self._credential
        
        # Try RBAC first
        try:
            self._credential = DefaultAzureCredential()
            return self._credential
        except Exception:
            pass
        
        # Fall back to API key
        if app_settings.search and app_settings.search.admin_key:
            self._credential = AzureKeyCredential(app_settings.search.admin_key)
            return self._credential
        
        raise ValueError("No valid search credentials available")
    
    def _get_products_client(self) -> SearchClient:
        """Get or create the products search client."""
        if self._products_client is None:
            if not app_settings.search or not app_settings.search.endpoint:
                raise ValueError("Azure AI Search endpoint not configured")
            
            self._products_client = SearchClient(
                endpoint=app_settings.search.endpoint,
                index_name=app_settings.search.products_index,
                credential=self._get_credential()
            )
        return self._products_client
    
    def _get_images_client(self) -> SearchClient:
        """Get or create the images search client."""
        if self._images_client is None:
            if not app_settings.search or not app_settings.search.endpoint:
                raise ValueError("Azure AI Search endpoint not configured")
            
            self._images_client = SearchClient(
                endpoint=app_settings.search.endpoint,
                index_name=app_settings.search.images_index,
                credential=self._get_credential()
            )
        return self._images_client
    
    async def search_products(
        self,
        query: str,
        category: Optional[str] = None,
        sub_category: Optional[str] = None,
        top: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Search for products using Azure AI Search.
        
        Args:
            query: Search query text
            category: Optional category filter
            sub_category: Optional sub-category filter
            top: Maximum number of results
        
        Returns:
            List of matching products
        """
        try:
            client = self._get_products_client()
            
            # Build filter
            filters = []
            if category:
                filters.append(f"category eq '{category}'")
            if sub_category:
                filters.append(f"sub_category eq '{sub_category}'")
            
            filter_str = " and ".join(filters) if filters else None
            
            # Execute search
            results = client.search(
                search_text=query,
                filter=filter_str,
                top=top,
                select=["id", "product_name", "sku", "model", "category", "sub_category",
                       "marketing_description", "detailed_spec_description", "image_description"]
            )
            
            products = []
            for result in results:
                products.append({
                    "id": result.get("id"),
                    "product_name": result.get("product_name"),
                    "sku": result.get("sku"),
                    "model": result.get("model"),
                    "category": result.get("category"),
                    "sub_category": result.get("sub_category"),
                    "marketing_description": result.get("marketing_description"),
                    "detailed_spec_description": result.get("detailed_spec_description"),
                    "image_description": result.get("image_description"),
                    "search_score": result.get("@search.score")
                })
            
            logger.info(f"Product search for '{query}' returned {len(products)} results")
            return products
            
        except Exception as e:
            logger.error(f"Product search failed: {e}")
            return []
    
    async def search_images(
        self,
        query: str,
        color_family: Optional[str] = None,
        mood: Optional[str] = None,
        top: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Search for images/color palettes using Azure AI Search.
        
        Args:
            query: Search query (color, mood, style keywords)
            color_family: Optional color family filter (Cool, Warm, Neutral, etc.)
            mood: Optional mood filter
            top: Maximum number of results
        
        Returns:
            List of matching images with metadata
        """
        try:
            client = self._get_images_client()
            
            # Build filter
            filters = []
            if color_family:
                filters.append(f"color_family eq '{color_family}'")
            
            filter_str = " and ".join(filters) if filters else None
            
            # Execute search
            results = client.search(
                search_text=query,
                filter=filter_str,
                top=top,
                select=["id", "name", "filename", "primary_color", "secondary_color",
                       "color_family", "mood", "style", "description", "use_cases",
                       "blob_url", "keywords"]
            )
            
            images = []
            for result in results:
                images.append({
                    "id": result.get("id"),
                    "name": result.get("name"),
                    "filename": result.get("filename"),
                    "primary_color": result.get("primary_color"),
                    "secondary_color": result.get("secondary_color"),
                    "color_family": result.get("color_family"),
                    "mood": result.get("mood"),
                    "style": result.get("style"),
                    "description": result.get("description"),
                    "use_cases": result.get("use_cases"),
                    "blob_url": result.get("blob_url"),
                    "keywords": result.get("keywords"),
                    "search_score": result.get("@search.score")
                })
            
            logger.info(f"Image search for '{query}' returned {len(images)} results")
            return images
            
        except Exception as e:
            logger.error(f"Image search failed: {e}")
            return []
    
    async def get_grounding_context(
        self,
        product_query: str,
        image_query: Optional[str] = None,
        category: Optional[str] = None,
        mood: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get combined grounding context for content generation.
        
        Searches both products and images to provide comprehensive
        context for AI content generation.
        
        Args:
            product_query: Query for product search
            image_query: Optional query for image/style search
            category: Optional product category filter
            mood: Optional mood/style filter for images
        
        Returns:
            Combined grounding context with products and images
        """
        # Search products
        products = await self.search_products(
            query=product_query,
            category=category,
            top=5
        )
        
        # Search images if query provided
        images = []
        if image_query:
            images = await self.search_images(
                query=image_query,
                mood=mood,
                top=3
            )
        
        # Build grounding context
        context = {
            "products": products,
            "images": images,
            "product_count": len(products),
            "image_count": len(images),
            "grounding_summary": self._build_grounding_summary(products, images)
        }
        
        return context
    
    def _build_grounding_summary(
        self,
        products: List[Dict[str, Any]],
        images: List[Dict[str, Any]]
    ) -> str:
        """Build a text summary of grounding context for agents."""
        parts = []
        
        if products:
            parts.append("## Available Products\n")
            for p in products[:5]:
                parts.append(f"- **{p.get('product_name')}** ({p.get('sku')})")
                parts.append(f"  Category: {p.get('category')} > {p.get('sub_category')}")
                parts.append(f"  Marketing: {p.get('marketing_description', '')[:150]}...")
                if p.get('image_description'):
                    parts.append(f"  Visual: {p.get('image_description', '')[:100]}...")
                parts.append("")
        
        if images:
            parts.append("\n## Available Visual Styles\n")
            for img in images[:3]:
                parts.append(f"- **{img.get('name')}**")
                parts.append(f"  Colors: {img.get('primary_color')}, {img.get('secondary_color')}")
                parts.append(f"  Mood: {img.get('mood')}")
                parts.append(f"  Style: {img.get('style')}")
                parts.append(f"  Best for: {img.get('use_cases', '')[:100]}")
                parts.append("")
        
        return "\n".join(parts)


# Global service instance
_search_service: Optional[SearchService] = None


async def get_search_service() -> SearchService:
    """Get or create the search service instance."""
    global _search_service
    if _search_service is None:
        _search_service = SearchService()
    return _search_service
