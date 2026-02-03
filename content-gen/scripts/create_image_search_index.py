"""
Create Azure AI Search Index for Image Grounding.

This script creates a search index for product images with:
- Image metadata (name, description, colors, style)
- Vector embeddings for semantic search
- Blob storage integration for image retrieval

Uses DefaultAzureCredential for authentication (RBAC).
"""

import asyncio
import json
import os
import sys
from pathlib import Path
from typing import List, Dict, Any

from azure.identity import DefaultAzureCredential
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchIndex,
    SearchField,
    SearchFieldDataType,
    SimpleField,
    SearchableField,
    VectorSearch,
    VectorSearchProfile,
    HnswAlgorithmConfiguration,
    SemanticConfiguration,
    SemanticField,
    SemanticPrioritizedFields,
    SemanticSearch,
)
from azure.core.credentials import AzureKeyCredential
from azure.storage.blob.aio import BlobServiceClient
from dotenv import load_dotenv

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Load environment variables
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

# Configuration
SEARCH_ENDPOINT = os.getenv("AZURE_AI_SEARCH_ENDPOINT", "https://search-contentgen-jh.search.windows.net")
SEARCH_INDEX_NAME = os.getenv("AZURE_AI_SEARCH_IMAGE_INDEX", "product-images")
STORAGE_ACCOUNT_NAME = os.getenv("AZURE_BLOB_ACCOUNT_NAME", "storagecontentgenjh")
CONTAINER_NAME = os.getenv("AZURE_BLOB_PRODUCT_IMAGES_CONTAINER", "product-images")

AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT", "")
AZURE_OPENAI_EMBEDDING_MODEL = os.getenv("AZURE_OPENAI_EMBEDDING_MODEL", "text-embedding-ada-002")
AZURE_SEARCH_ADMIN_KEY = os.getenv("AZURE_AI_SEARCH_ADMIN_KEY", "")

# Image metadata - derived from filenames with color/style info
IMAGE_METADATA = {
    "BlueAsh.jpg": {
        "name": "BlueAsh",
        "primary_color": "Blue",
        "secondary_color": "Gray",
        "color_family": "Cool",
        "mood": "Calm, Professional",
        "style": "Modern, Minimalist",
        "description": "A sophisticated blue-ash tone with subtle gray undertones. Perfect for professional and calming aesthetics.",
        "use_cases": "Corporate branding, tech products, wellness, professional services",
        "keywords": ["blue", "ash", "gray", "calm", "professional", "modern", "cool tones"]
    },
    "CloudDrift.jpg": {
        "name": "CloudDrift",
        "primary_color": "White",
        "secondary_color": "Light Gray",
        "color_family": "Neutral",
        "mood": "Ethereal, Peaceful",
        "style": "Soft, Dreamy",
        "description": "A soft, cloudy white with gentle drifting patterns. Evokes serenity and openness.",
        "use_cases": "Spa, wellness, bedding, clean beauty, minimalist design",
        "keywords": ["white", "cloud", "soft", "peaceful", "ethereal", "clean", "neutral"]
    },
    "FogHarbor.jpg": {
        "name": "FogHarbor",
        "primary_color": "Gray",
        "secondary_color": "Blue-Gray",
        "color_family": "Cool",
        "mood": "Mysterious, Coastal",
        "style": "Moody, Atmospheric",
        "description": "A misty gray reminiscent of coastal fog rolling into harbor. Mysterious yet inviting.",
        "use_cases": "Nautical themes, outdoor gear, photography, artisanal products",
        "keywords": ["fog", "gray", "harbor", "coastal", "misty", "moody", "atmospheric"]
    },
    "GlacierTint.jpg": {
        "name": "GlacierTint",
        "primary_color": "Ice Blue",
        "secondary_color": "White",
        "color_family": "Cool",
        "mood": "Fresh, Crisp",
        "style": "Clean, Nordic",
        "description": "A crisp ice-blue tint inspired by glacial formations. Fresh and invigorating.",
        "use_cases": "Skincare, beverages, winter sports, Scandinavian design",
        "keywords": ["glacier", "ice", "blue", "fresh", "crisp", "nordic", "winter"]
    },
    "GraphiteFade.jpg": {
        "name": "GraphiteFade",
        "primary_color": "Dark Gray",
        "secondary_color": "Charcoal",
        "color_family": "Dark",
        "mood": "Sophisticated, Bold",
        "style": "Industrial, Premium",
        "description": "A deep graphite with gradient fade effect. Sophisticated and premium feel.",
        "use_cases": "Luxury goods, electronics, automotive, high-end fashion",
        "keywords": ["graphite", "dark", "gray", "sophisticated", "premium", "industrial", "bold"]
    },
    "ObsidianPearl.jpg": {
        "name": "ObsidianPearl",
        "primary_color": "Black",
        "secondary_color": "Pearl White",
        "color_family": "Contrast",
        "mood": "Elegant, Luxurious",
        "style": "High-contrast, Dramatic",
        "description": "A striking contrast of deep obsidian black with pearlescent highlights. Ultimate elegance.",
        "use_cases": "Jewelry, luxury accessories, evening wear, premium packaging",
        "keywords": ["obsidian", "pearl", "black", "white", "elegant", "luxurious", "contrast"]
    },
    "OliveStone.jpg": {
        "name": "OliveStone",
        "primary_color": "Olive Green",
        "secondary_color": "Brown",
        "color_family": "Earth",
        "mood": "Natural, Grounded",
        "style": "Organic, Rustic",
        "description": "An earthy olive green with stone-like undertones. Natural and grounded aesthetic.",
        "use_cases": "Organic products, outdoor brands, home decor, sustainable fashion",
        "keywords": ["olive", "green", "stone", "earth", "natural", "grounded", "organic"]
    },
    "PineShadow.jpg": {
        "name": "PineShadow",
        "primary_color": "Dark Green",
        "secondary_color": "Forest Green",
        "color_family": "Nature",
        "mood": "Deep, Mysterious",
        "style": "Natural, Rich",
        "description": "A deep pine green with shadowy depth. Evokes dense forests and natural mystery.",
        "use_cases": "Outdoor recreation, eco brands, luxury camping, artisan products",
        "keywords": ["pine", "forest", "green", "shadow", "deep", "natural", "mysterious"]
    },
    "PorcelainMist.jpg": {
        "name": "PorcelainMist",
        "primary_color": "Cream",
        "secondary_color": "Soft White",
        "color_family": "Warm Neutral",
        "mood": "Delicate, Refined",
        "style": "Classic, Elegant",
        "description": "A delicate porcelain cream with misty softness. Classic elegance and refinement.",
        "use_cases": "Ceramics, fine dining, bridal, luxury stationery",
        "keywords": ["porcelain", "cream", "mist", "delicate", "refined", "classic", "elegant"]
    },
    "QuietMoss.jpg": {
        "name": "QuietMoss",
        "primary_color": "Moss Green",
        "secondary_color": "Sage",
        "color_family": "Nature",
        "mood": "Tranquil, Peaceful",
        "style": "Organic, Calming",
        "description": "A quiet moss green that brings tranquility and connection to nature.",
        "use_cases": "Wellness brands, botanical products, sustainable goods, meditation spaces",
        "keywords": ["moss", "green", "quiet", "tranquil", "peaceful", "organic", "calming"]
    },
    "SeafoamLight.jpg": {
        "name": "SeafoamLight",
        "primary_color": "Seafoam",
        "secondary_color": "Mint",
        "color_family": "Cool",
        "mood": "Fresh, Playful",
        "style": "Coastal, Light",
        "description": "A light seafoam with minty freshness. Playful yet sophisticated coastal vibe.",
        "use_cases": "Summer collections, beach products, refreshing beverages, youth brands",
        "keywords": ["seafoam", "mint", "light", "fresh", "playful", "coastal", "summer"]
    },
    "SilverShore.jpg": {
        "name": "SilverShore",
        "primary_color": "Silver",
        "secondary_color": "Sand",
        "color_family": "Metallic Neutral",
        "mood": "Sophisticated, Modern",
        "style": "Sleek, Contemporary",
        "description": "A sleek silver with sandy shore warmth. Modern sophistication meets coastal warmth.",
        "use_cases": "Tech accessories, modern home, jewelry, premium retail",
        "keywords": ["silver", "shore", "sand", "sophisticated", "modern", "sleek", "metallic"]
    },
    "SnowVeil.jpg": {
        "name": "SnowVeil",
        "primary_color": "Pure White",
        "secondary_color": "Ice",
        "color_family": "Cool Neutral",
        "mood": "Pure, Serene",
        "style": "Minimal, Clean",
        "description": "A pure snow white with delicate veil-like softness. Ultimate purity and serenity.",
        "use_cases": "Bridal, skincare, clean tech, medical, minimalist design",
        "keywords": ["snow", "white", "pure", "serene", "minimal", "clean", "veil"]
    },
    "SteelSky.jpg": {
        "name": "SteelSky",
        "primary_color": "Steel Blue",
        "secondary_color": "Gray",
        "color_family": "Cool",
        "mood": "Strong, Reliable",
        "style": "Industrial, Modern",
        "description": "A strong steel blue with sky-like openness. Combines strength with aspiration.",
        "use_cases": "Automotive, aerospace, industrial design, corporate, sports gear",
        "keywords": ["steel", "blue", "sky", "strong", "reliable", "industrial", "modern"]
    },
    "StoneDusk.jpg": {
        "name": "StoneDusk",
        "primary_color": "Warm Gray",
        "secondary_color": "Taupe",
        "color_family": "Warm Neutral",
        "mood": "Warm, Inviting",
        "style": "Rustic, Cozy",
        "description": "A warm stone gray with dusk-like golden undertones. Inviting and comfortable.",
        "use_cases": "Home decor, hospitality, artisan goods, coffee shops",
        "keywords": ["stone", "dusk", "warm", "gray", "taupe", "inviting", "cozy"]
    },
    "VerdantHaze.jpg": {
        "name": "VerdantHaze",
        "primary_color": "Green",
        "secondary_color": "Teal",
        "color_family": "Nature",
        "mood": "Lush, Vibrant",
        "style": "Tropical, Fresh",
        "description": "A lush verdant green with hazy tropical depth. Vibrant and full of life.",
        "use_cases": "Tropical products, plant-based brands, health foods, spa resorts",
        "keywords": ["verdant", "green", "haze", "lush", "vibrant", "tropical", "fresh"]
    }
}


def create_search_index(index_client: SearchIndexClient) -> SearchIndex:
    """Create the search index schema for product images."""
    
    fields = [
        # Key field
        SimpleField(
            name="id",
            type=SearchFieldDataType.String,
            key=True,
            filterable=True
        ),
        # Image identification
        SearchableField(
            name="filename",
            type=SearchFieldDataType.String,
            filterable=True,
            sortable=True
        ),
        SearchableField(
            name="name",
            type=SearchFieldDataType.String,
            filterable=True,
            sortable=True
        ),
        # Color fields
        SearchableField(
            name="primary_color",
            type=SearchFieldDataType.String,
            filterable=True,
            facetable=True
        ),
        SearchableField(
            name="secondary_color",
            type=SearchFieldDataType.String,
            filterable=True,
            facetable=True
        ),
        SearchableField(
            name="color_family",
            type=SearchFieldDataType.String,
            filterable=True,
            facetable=True
        ),
        # Style and mood
        SearchableField(
            name="mood",
            type=SearchFieldDataType.String,
            filterable=True
        ),
        SearchableField(
            name="style",
            type=SearchFieldDataType.String,
            filterable=True
        ),
        # Description and use cases
        SearchableField(
            name="description",
            type=SearchFieldDataType.String
        ),
        SearchableField(
            name="use_cases",
            type=SearchFieldDataType.String
        ),
        # Keywords for search
        SimpleField(
            name="keywords",
            type=SearchFieldDataType.Collection(SearchFieldDataType.String),
            filterable=True,
            facetable=True
        ),
        # Storage info
        SimpleField(
            name="blob_url",
            type=SearchFieldDataType.String
        ),
        SimpleField(
            name="blob_container",
            type=SearchFieldDataType.String,
            filterable=True
        ),
        # Combined text for embedding
        SearchableField(
            name="combined_text",
            type=SearchFieldDataType.String
        ),
        # Vector field for semantic search
        SearchField(
            name="content_vector",
            type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
            searchable=True,
            vector_search_dimensions=1536,  # text-embedding-ada-002 dimensions
            vector_search_profile_name="image-vector-profile"
        )
    ]
    
    # Configure vector search
    vector_search = VectorSearch(
        algorithms=[
            HnswAlgorithmConfiguration(
                name="hnsw-algorithm",
                parameters={
                    "m": 4,
                    "efConstruction": 400,
                    "efSearch": 500,
                    "metric": "cosine"
                }
            )
        ],
        profiles=[
            VectorSearchProfile(
                name="image-vector-profile",
                algorithm_configuration_name="hnsw-algorithm"
            )
        ]
    )
    
    # Configure semantic search
    semantic_config = SemanticConfiguration(
        name="image-semantic-config",
        prioritized_fields=SemanticPrioritizedFields(
            title_field=SemanticField(field_name="name"),
            content_fields=[
                SemanticField(field_name="description"),
                SemanticField(field_name="use_cases"),
                SemanticField(field_name="combined_text")
            ],
            keywords_fields=[
                SemanticField(field_name="primary_color"),
                SemanticField(field_name="style"),
                SemanticField(field_name="mood")
            ]
        )
    )
    
    semantic_search = SemanticSearch(configurations=[semantic_config])
    
    # Create the index
    index = SearchIndex(
        name=SEARCH_INDEX_NAME,
        fields=fields,
        vector_search=vector_search,
        semantic_search=semantic_search
    )
    
    return index


async def get_embedding(text: str) -> List[float]:
    """Get embedding vector for text using Azure OpenAI."""
    from openai import AzureOpenAI
    
    client = AzureOpenAI(
        azure_endpoint=AZURE_OPENAI_ENDPOINT,
        azure_ad_token_provider=lambda: DefaultAzureCredential().get_token(
            "https://cognitiveservices.azure.com/.default"
        ).token,
        api_version="2024-06-01"
    )
    
    try:
        response = client.embeddings.create(
            input=text,
            model=AZURE_OPENAI_EMBEDDING_MODEL
        )
        return response.data[0].embedding
    except Exception as e:
        print(f"Warning: Could not generate embedding: {e}")
        # Return zero vector as fallback
        return [0.0] * 1536


async def get_blob_images() -> List[Dict[str, Any]]:
    """Get list of images from blob storage."""
    account_url = f"https://{STORAGE_ACCOUNT_NAME}.blob.core.windows.net"
    credential = DefaultAzureCredential()
    
    images = []
    
    async with BlobServiceClient(account_url=account_url, credential=credential) as blob_service:
        container_client = blob_service.get_container_client(CONTAINER_NAME)
        
        async for blob in container_client.list_blobs():
            if blob.name.lower().endswith(('.jpg', '.jpeg')):
                images.append({
                    "filename": blob.name,
                    "url": f"{account_url}/{CONTAINER_NAME}/{blob.name}",
                    "size": blob.size
                })
    
    return images


def prepare_document(filename: str, blob_url: str) -> Dict[str, Any]:
    """Prepare a document for indexing."""
    
    # Get metadata for this image
    metadata = IMAGE_METADATA.get(filename, {
        "name": filename.replace(".jpg", "").replace(".JPG", ""),
        "primary_color": "Unknown",
        "secondary_color": "Unknown",
        "color_family": "Unknown",
        "mood": "Unknown",
        "style": "Unknown",
        "description": f"Image file: {filename}",
        "use_cases": "General marketing",
        "keywords": [filename.lower().replace(".jpg", "")]
    })
    
    # Create combined text for embedding
    combined_text = f"""
    {metadata['name']} - {metadata['description']}
    Colors: {metadata['primary_color']}, {metadata['secondary_color']} ({metadata['color_family']})
    Mood: {metadata['mood']}
    Style: {metadata['style']}
    Use Cases: {metadata['use_cases']}
    Keywords: {', '.join(metadata['keywords'])}
    """
    
    # Create document ID from filename
    doc_id = filename.lower().replace(".jpg", "").replace(" ", "-").replace(".", "-")
    
    return {
        "id": doc_id,
        "filename": filename,
        "name": metadata["name"],
        "primary_color": metadata["primary_color"],
        "secondary_color": metadata["secondary_color"],
        "color_family": metadata["color_family"],
        "mood": metadata["mood"],
        "style": metadata["style"],
        "description": metadata["description"],
        "use_cases": metadata["use_cases"],
        "keywords": metadata["keywords"],
        "blob_url": blob_url,
        "blob_container": CONTAINER_NAME,
        "combined_text": combined_text.strip()
    }


async def index_images(search_client: SearchClient, images: List[Dict[str, Any]], use_vectors: bool = True):
    """Index images into the search index."""
    
    documents = []
    
    for img in images:
        doc = prepare_document(img["filename"], img["url"])
        
        if use_vectors:
            try:
                # Generate embedding for the combined text
                embedding = await get_embedding(doc["combined_text"])
                doc["content_vector"] = embedding
                print(f"  ✓ Generated embedding for: {img['filename']}")
            except Exception as e:
                print(f"  ⚠ Embedding failed for {img['filename']}: {e}")
                doc["content_vector"] = [0.0] * 1536
        else:
            doc["content_vector"] = [0.0] * 1536
        
        documents.append(doc)
    
    # Upload documents to the index
    result = search_client.upload_documents(documents)
    
    succeeded = sum(1 for r in result if r.succeeded)
    failed = sum(1 for r in result if not r.succeeded)
    
    return succeeded, failed


async def main():
    """Main entry point."""
    print("=" * 60)
    print("Azure AI Search Index Creation for Product Images")
    print("=" * 60)
    print()
    
    # Check for embedding model deployment
    use_vectors = bool(AZURE_OPENAI_ENDPOINT) and bool(AZURE_OPENAI_EMBEDDING_MODEL)
    if not use_vectors:
        print("⚠ Warning: Azure OpenAI not configured. Creating index without embeddings.")
        print("  Set AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_EMBEDDING_MODEL in .env")
        print()
    
    # Prefer RBAC (DefaultAzureCredential), fall back to API key if RBAC fails
    try:
        search_credential = DefaultAzureCredential()
        # Test the credential
        test_client = SearchIndexClient(endpoint=SEARCH_ENDPOINT, credential=search_credential)
        list(test_client.list_indexes())  # Quick test
        print("Using RBAC authentication for search (DefaultAzureCredential)")
    except Exception as e:
        if AZURE_SEARCH_ADMIN_KEY:
            search_credential = AzureKeyCredential(AZURE_SEARCH_ADMIN_KEY)
            print("Using API key authentication for search (RBAC failed)")
        else:
            print(f"⚠ RBAC failed and no API key configured: {e}")
            raise
    
    # Create index client
    index_client = SearchIndexClient(
        endpoint=SEARCH_ENDPOINT,
        credential=search_credential
    )
    
    # Create or update the index
    print(f"Creating search index: {SEARCH_INDEX_NAME}")
    print(f"Search endpoint: {SEARCH_ENDPOINT}")
    print()
    
    try:
        index = create_search_index(index_client)
        result = index_client.create_or_update_index(index)
        print(f"✓ Index '{result.name}' created/updated successfully")
    except Exception as e:
        print(f"✗ Failed to create index: {e}")
        raise
    
    # Get images from blob storage
    print()
    print("Fetching images from blob storage...")
    
    try:
        images = await get_blob_images()
        print(f"Found {len(images)} images in blob storage")
    except Exception as e:
        print(f"✗ Failed to list blob images: {e}")
        print("  Make sure images are uploaded to blob storage first.")
        print("  Run: python upload_images.py")
        return
    
    if not images:
        print("No images found. Please upload images first using upload_images.py")
        return
    
    # Index the images
    print()
    print("Indexing images...")
    print("-" * 50)
    
    search_client = SearchClient(
        endpoint=SEARCH_ENDPOINT,
        index_name=SEARCH_INDEX_NAME,
        credential=search_credential
    )
    
    try:
        succeeded, failed = await index_images(search_client, images, use_vectors=use_vectors)
        print("-" * 50)
        print(f"\n✓ Indexed {succeeded} images successfully")
        if failed > 0:
            print(f"✗ Failed to index {failed} images")
    except Exception as e:
        print(f"✗ Failed to index images: {e}")
        raise
    
    # Summary
    print()
    print("=" * 60)
    print("Index Creation Complete!")
    print("=" * 60)
    print(f"Index name: {SEARCH_INDEX_NAME}")
    print(f"Endpoint: {SEARCH_ENDPOINT}")
    print(f"Documents indexed: {succeeded}")
    print()
    print("You can now use this index for grounding AI content generation.")
    print()
    print("Example search queries:")
    print("  - Search by color: 'blue', 'green', 'warm tones'")
    print("  - Search by mood: 'calm', 'energetic', 'professional'")
    print("  - Search by use case: 'luxury products', 'outdoor brands'")


if __name__ == "__main__":
    asyncio.run(main())
