#!/usr/bin/env python3
"""
Product Data Ingestion Script for Intelligent Content Generation Accelerator

This script handles:
1. Loading product data from CSV/JSON files
2. Uploading product images to Azure Blob Storage
3. Indexing product data in Azure AI Search
4. Storing product metadata in Azure Cosmos DB

Usage:
    python product_ingestion.py --data-path ./sample_data --env-file .env

Requirements:
    - Azure credentials configured (via environment or managed identity)
    - Required environment variables set in .env or Azure Key Vault
"""

import argparse
import asyncio
import json
import logging
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@dataclass
class ProductData:
    """Product data model."""
    id: str
    name: str
    description: str
    category: str
    price: float
    image_url: str = ""
    attributes: dict = field(default_factory=dict)
    tags: list = field(default_factory=list)


@dataclass
class IngestionConfig:
    """Configuration for product ingestion."""
    storage_account_name: str
    storage_container_name: str
    cosmos_endpoint: str
    cosmos_database: str
    cosmos_container: str
    search_service_name: str
    search_index_name: str
    data_path: Path
    batch_size: int = 100


def load_environment(env_file: str | None = None) -> IngestionConfig:
    """Load configuration from environment variables or .env file."""
    if env_file and Path(env_file).exists():
        from dotenv import load_dotenv
        load_dotenv(env_file)
        logger.info(f"Loaded environment from {env_file}")
    
    return IngestionConfig(
        storage_account_name=os.getenv("AZURE_BLOB_ACCOUNT_NAME", ""),
        storage_container_name=os.getenv("AZURE_BLOB_PRODUCT_IMAGES_CONTAINER", "product-images"),
        cosmos_endpoint=os.getenv("AZURE_COSMOS_ENDPOINT", ""),
        cosmos_database=os.getenv("AZURE_COSMOS_DATABASE_NAME", "content_generation_db"),
        cosmos_container=os.getenv("AZURE_COSMOS_PRODUCTS_CONTAINER", "products"),
        search_service_name=os.getenv("AI_SEARCH_SERVICE_NAME", ""),
        search_index_name=os.getenv("AZURE_AI_SEARCH_PRODUCTS_INDEX", "product_index"),
        data_path=Path(os.getenv("DATA_PATH", "./sample_data")),
        batch_size=int(os.getenv("BATCH_SIZE", "100"))
    )


def validate_config(config: IngestionConfig) -> bool:
    """Validate configuration has required values."""
    required_fields = [
        ("storage_account_name", config.storage_account_name),
        ("cosmos_endpoint", config.cosmos_endpoint),
        ("search_service_name", config.search_service_name),
    ]
    
    missing = [name for name, value in required_fields if not value]
    
    if missing:
        logger.error(f"Missing required configuration: {', '.join(missing)}")
        return False
    
    if not config.data_path.exists():
        logger.error(f"Data path does not exist: {config.data_path}")
        return False
    
    return True


def load_products_from_json(file_path: Path) -> list[ProductData]:
    """Load products from a JSON file."""
    logger.info(f"Loading products from {file_path}")
    
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    products = []
    items = data if isinstance(data, list) else data.get("products", [])
    
    for item in items:
        products.append(ProductData(
            id=str(item.get("id", "")),
            name=item.get("name", ""),
            description=item.get("description", ""),
            category=item.get("category", ""),
            price=float(item.get("price", 0.0)),
            image_url=item.get("image_url", ""),
            attributes=item.get("attributes", {}),
            tags=item.get("tags", [])
        ))
    
    logger.info(f"Loaded {len(products)} products from {file_path.name}")
    return products


def load_products_from_csv(file_path: Path) -> list[ProductData]:
    """Load products from a CSV file."""
    import csv
    
    logger.info(f"Loading products from {file_path}")
    products = []
    
    with open(file_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            products.append(ProductData(
                id=str(row.get("id", "")),
                name=row.get("name", ""),
                description=row.get("description", ""),
                category=row.get("category", ""),
                price=float(row.get("price", 0.0)),
                image_url=row.get("image_url", ""),
                attributes=json.loads(row.get("attributes", "{}")),
                tags=row.get("tags", "").split(",") if row.get("tags") else []
            ))
    
    logger.info(f"Loaded {len(products)} products from {file_path.name}")
    return products


def load_all_products(data_path: Path) -> list[ProductData]:
    """Load all products from JSON and CSV files in the data directory."""
    products = []
    
    # Load JSON files
    for json_file in data_path.glob("*.json"):
        try:
            products.extend(load_products_from_json(json_file))
        except Exception as e:
            logger.error(f"Error loading {json_file}: {e}")
    
    # Load CSV files
    for csv_file in data_path.glob("*.csv"):
        try:
            products.extend(load_products_from_csv(csv_file))
        except Exception as e:
            logger.error(f"Error loading {csv_file}: {e}")
    
    logger.info(f"Total products loaded: {len(products)}")
    return products


async def upload_images_to_blob(
    config: IngestionConfig,
    products: list[ProductData],
    images_path: Path | None = None
) -> list[ProductData]:
    """Upload product images to Azure Blob Storage."""
    try:
        from azure.identity import DefaultAzureCredential
        from azure.storage.blob.aio import BlobServiceClient
    except ImportError:
        logger.warning("Azure storage SDK not installed. Skipping image upload.")
        return products
    
    if images_path is None:
        images_path = config.data_path / "images"
    
    if not images_path.exists():
        logger.info(f"Images path {images_path} does not exist. Skipping image upload.")
        return products
    
    credential = DefaultAzureCredential()
    account_url = f"https://{config.storage_account_name}.blob.core.windows.net"
    
    async with BlobServiceClient(account_url, credential) as blob_service:
        container_client = blob_service.get_container_client(config.storage_container_name)
        
        for product in products:
            # Check for local image file
            image_extensions = [".jpg", ".jpeg", ".png", ".gif", ".webp"]
            for ext in image_extensions:
                local_image = images_path / f"{product.id}{ext}"
                if local_image.exists():
                    blob_name = f"{product.id}{ext}"
                    blob_client = container_client.get_blob_client(blob_name)
                    
                    with open(local_image, "rb") as data:
                        await blob_client.upload_blob(data, overwrite=True)
                    
                    product.image_url = f"{account_url}/{config.storage_container_name}/{blob_name}"
                    logger.debug(f"Uploaded image for product {product.id}")
                    break
    
    logger.info(f"Image upload completed for {len(products)} products")
    return products


async def index_products_in_search(
    config: IngestionConfig,
    products: list[ProductData]
) -> int:
    """Index products in Azure AI Search."""
    try:
        from azure.identity import DefaultAzureCredential
        from azure.search.documents import SearchClient
        from azure.search.documents.indexes import SearchIndexClient
        from azure.search.documents.indexes.models import (
            SearchIndex,
            SearchableField,
            SimpleField,
            SearchFieldDataType,
            SemanticConfiguration,
            SemanticField,
            SemanticPrioritizedFields,
            SemanticSearch,
        )
    except ImportError:
        logger.error("Azure search SDK not installed. Cannot index products.")
        return 0
    
    credential = DefaultAzureCredential()
    endpoint = f"https://{config.search_service_name}.search.windows.net"
    
    # Create or update the search index
    index_client = SearchIndexClient(endpoint, credential)
    
    fields = [
        SimpleField(name="id", type=SearchFieldDataType.String, key=True),
        SearchableField(name="name", type=SearchFieldDataType.String),
        SearchableField(name="description", type=SearchFieldDataType.String),
        SearchableField(name="category", type=SearchFieldDataType.String, filterable=True, facetable=True),
        SimpleField(name="price", type=SearchFieldDataType.Double, filterable=True, sortable=True),
        SimpleField(name="image_url", type=SearchFieldDataType.String),
        SearchableField(name="tags", type=SearchFieldDataType.Collection(SearchFieldDataType.String), filterable=True),
    ]
    
    semantic_config = SemanticConfiguration(
        name="my-semantic-config",
        prioritized_fields=SemanticPrioritizedFields(
            title_field=SemanticField(field_name="name"),
            content_fields=[SemanticField(field_name="description")],
            keywords_fields=[SemanticField(field_name="tags")]
        )
    )
    
    semantic_search = SemanticSearch(configurations=[semantic_config])
    
    index = SearchIndex(
        name=config.search_index_name,
        fields=fields,
        semantic_search=semantic_search
    )
    
    index_client.create_or_update_index(index)
    logger.info(f"Created/updated search index: {config.search_index_name}")
    
    # Upload documents in batches
    search_client = SearchClient(endpoint, config.search_index_name, credential)
    
    documents = [
        {
            "id": p.id,
            "name": p.name,
            "description": p.description,
            "category": p.category,
            "price": p.price,
            "image_url": p.image_url,
            "tags": p.tags
        }
        for p in products
    ]
    
    indexed_count = 0
    for i in range(0, len(documents), config.batch_size):
        batch = documents[i:i + config.batch_size]
        result = search_client.upload_documents(batch)
        indexed_count += len([r for r in result if r.succeeded])
        logger.info(f"Indexed batch {i // config.batch_size + 1}: {len(batch)} documents")
    
    logger.info(f"Successfully indexed {indexed_count} products in Azure AI Search")
    return indexed_count


async def store_products_in_cosmos(
    config: IngestionConfig,
    products: list[ProductData]
) -> int:
    """Store product metadata in Azure Cosmos DB."""
    try:
        from azure.identity import DefaultAzureCredential
        from azure.cosmos.aio import CosmosClient
    except ImportError:
        logger.error("Azure Cosmos SDK not installed. Cannot store products.")
        return 0
    
    credential = DefaultAzureCredential()
    endpoint = f"https://{config.cosmos_endpoint}.documents.azure.com:443/"
    
    async with CosmosClient(endpoint, credential) as client:
        database = client.get_database_client(config.cosmos_database)
        container = database.get_container_client(config.cosmos_container)
        
        stored_count = 0
        for product in products:
            item = {
                "id": product.id,
                "name": product.name,
                "description": product.description,
                "category": product.category,
                "price": product.price,
                "image_url": product.image_url,
                "attributes": product.attributes,
                "tags": product.tags
            }
            
            try:
                await container.upsert_item(item)
                stored_count += 1
            except Exception as e:
                logger.error(f"Failed to store product {product.id}: {e}")
        
        logger.info(f"Successfully stored {stored_count} products in Cosmos DB")
        return stored_count


async def run_ingestion(config: IngestionConfig) -> dict[str, Any]:
    """Run the full product ingestion pipeline."""
    results = {
        "products_loaded": 0,
        "images_uploaded": 0,
        "products_indexed": 0,
        "products_stored": 0,
        "errors": []
    }
    
    # Step 1: Load products
    products = load_all_products(config.data_path)
    results["products_loaded"] = len(products)
    
    if not products:
        logger.warning("No products found to ingest")
        return results
    
    # Step 2: Upload images
    try:
        products = await upload_images_to_blob(config, products)
        results["images_uploaded"] = len([p for p in products if p.image_url])
    except Exception as e:
        logger.error(f"Image upload failed: {e}")
        results["errors"].append(f"Image upload: {str(e)}")
    
    # Step 3: Index in AI Search
    try:
        results["products_indexed"] = await index_products_in_search(config, products)
    except Exception as e:
        logger.error(f"Search indexing failed: {e}")
        results["errors"].append(f"Search indexing: {str(e)}")
    
    # Step 4: Store in Cosmos DB
    try:
        results["products_stored"] = await store_products_in_cosmos(config, products)
    except Exception as e:
        logger.error(f"Cosmos DB storage failed: {e}")
        results["errors"].append(f"Cosmos DB: {str(e)}")
    
    return results


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Product Data Ingestion for Content Generation Accelerator"
    )
    parser.add_argument(
        "--data-path",
        type=str,
        help="Path to the directory containing product data files"
    )
    parser.add_argument(
        "--env-file",
        type=str,
        default=".env",
        help="Path to .env file with configuration"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=100,
        help="Batch size for indexing operations"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Load configuration
    config = load_environment(args.env_file)
    
    # Override with command line arguments
    if args.data_path:
        config.data_path = Path(args.data_path)
    if args.batch_size:
        config.batch_size = args.batch_size
    
    # Validate configuration
    if not validate_config(config):
        logger.error("Configuration validation failed")
        sys.exit(1)
    
    # Run ingestion
    logger.info("Starting product ingestion...")
    results = asyncio.run(run_ingestion(config))
    
    # Print summary
    logger.info("=" * 50)
    logger.info("Ingestion Summary:")
    logger.info(f"  Products loaded: {results['products_loaded']}")
    logger.info(f"  Images uploaded: {results['images_uploaded']}")
    logger.info(f"  Products indexed: {results['products_indexed']}")
    logger.info(f"  Products stored: {results['products_stored']}")
    
    if results["errors"]:
        logger.warning(f"  Errors: {len(results['errors'])}")
        for error in results["errors"]:
            logger.warning(f"    - {error}")
    
    logger.info("=" * 50)
    
    # Exit with error code if there were failures
    if results["errors"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
