"""
Admin API Router - Provides administrative endpoints for data ingestion.

These endpoints are designed to be called from the post-deploy script
and run inside the VNet, bypassing firewall restrictions that block
direct access from external clients.

Endpoints:
- POST /api/admin/upload-images - Upload product images to Blob Storage
- POST /api/admin/load-sample-data - Load sample data to Cosmos DB
- POST /api/admin/create-search-index - Create/update the search index
"""

import base64
import logging
import os
from datetime import datetime, timezone
from quart import Blueprint, request, jsonify
from azure.storage.blob import ContentSettings

from settings import app_settings
from services.cosmos_service import get_cosmos_service
from services.blob_service import get_blob_service
from models import Product

logger = logging.getLogger(__name__)

# Create Blueprint for admin routes
admin_bp = Blueprint("admin", __name__, url_prefix="/api/admin")

# Admin API Key for authentication (optional but recommended)
ADMIN_API_KEY = os.environ.get("ADMIN_API_KEY", "")


def verify_admin_api_key() -> bool:
    """
    Verify the admin API key from request headers.
    
    If ADMIN_API_KEY is not set, all requests are allowed (development mode).
    If set, the request must include X-Admin-API-Key header with matching value.
    """
    if not ADMIN_API_KEY:
        # No API key configured - allow all requests (development/initial setup)
        return True
    
    provided_key = request.headers.get("X-Admin-API-Key", "")
    return provided_key == ADMIN_API_KEY


def unauthorized_response():
    """Return a 401 Unauthorized response."""
    return jsonify({
        "error": "Unauthorized",
        "message": "Invalid or missing X-Admin-API-Key header"
    }), 401


# ==================== Upload Images Endpoint ====================

@admin_bp.route("/upload-images", methods=["POST"])
async def upload_images():
    """
    Upload product images to Blob Storage.
    
    Request body:
    {
        "images": [
            {
                "filename": "SnowVeil.png",
                "content_type": "image/png",
                "data": "<base64-encoded-image-data>"
            },
            ...
        ]
    }
    
    Returns:
    {
        "success": true,
        "uploaded": 16,
        "failed": 0,
        "results": [
            {"filename": "SnowVeil.png", "status": "uploaded", "url": "..."},
            ...
        ]
    }
    """
    if not verify_admin_api_key():
        return unauthorized_response()
    
    try:
        data = await request.get_json()
        images = data.get("images", [])
        
        if not images:
            return jsonify({
                "error": "No images provided",
                "message": "Request body must contain 'images' array"
            }), 400
        
        blob_service = await get_blob_service()
        await blob_service.initialize()
        
        results = []
        uploaded_count = 0
        failed_count = 0
        
        for image_info in images:
            filename = image_info.get("filename", "")
            content_type = image_info.get("content_type", "image/png")
            image_data_b64 = image_info.get("data", "")
            
            if not filename or not image_data_b64:
                results.append({
                    "filename": filename or "unknown",
                    "status": "failed",
                    "error": "Missing filename or data"
                })
                failed_count += 1
                continue
            
            try:
                # Decode base64 image data
                image_data = base64.b64decode(image_data_b64)
                
                # Upload to product-images container
                blob_client = blob_service._product_images_container.get_blob_client(filename)
                await blob_client.upload_blob(
                    image_data,
                    overwrite=True,
                    content_settings=ContentSettings(content_type=content_type)
                )
                
                results.append({
                    "filename": filename,
                    "status": "uploaded",
                    "url": blob_client.url,
                    "size_bytes": len(image_data)
                })
                uploaded_count += 1
                logger.info(f"Uploaded image: {filename} ({len(image_data):,} bytes)")
                
            except Exception as e:
                logger.error(f"Failed to upload image {filename}: {e}")
                results.append({
                    "filename": filename,
                    "status": "failed",
                    "error": str(e)
                })
                failed_count += 1
        
        return jsonify({
            "success": failed_count == 0,
            "uploaded": uploaded_count,
            "failed": failed_count,
            "results": results
        })
        
    except Exception as e:
        logger.exception(f"Error in upload_images: {e}")
        return jsonify({
            "error": "Internal server error",
            "message": str(e)
        }), 500


# ==================== Load Sample Data Endpoint ====================

@admin_bp.route("/load-sample-data", methods=["POST"])
async def load_sample_data():
    """
    Load sample product data to Cosmos DB.
    
    Request body:
    {
        "products": [
            {
                "product_name": "Snow Veil",
                "description": "A crisp white paint...",
                "tags": "soft white, airy, minimal",
                "price": 59.95,
                "sku": "CP-0001",
                "image_url": "https://...",
                "category": "Paint"
            },
            ...
        ],
        "clear_existing": true  // Optional: delete existing products first
    }
    
    Returns:
    {
        "success": true,
        "loaded": 16,
        "failed": 0,
        "deleted": 5,  // If clear_existing was true
        "results": [
            {"sku": "CP-0001", "product_name": "Snow Veil", "status": "loaded"},
            ...
        ]
    }
    """
    if not verify_admin_api_key():
        return unauthorized_response()
    
    try:
        data = await request.get_json()
        products_data = data.get("products", [])
        clear_existing = data.get("clear_existing", False)
        
        if not products_data:
            return jsonify({
                "error": "No products provided",
                "message": "Request body must contain 'products' array"
            }), 400
        
        cosmos_service = await get_cosmos_service()
        
        deleted_count = 0
        if clear_existing:
            logger.info("Deleting existing products...")
            deleted_count = await cosmos_service.delete_all_products()
            logger.info(f"Deleted {deleted_count} existing products")
        
        results = []
        loaded_count = 0
        failed_count = 0
        
        for product_data in products_data:
            sku = product_data.get("sku", "")
            product_name = product_data.get("product_name", "")
            
            try:
                # Map incoming fields to Product model fields
                # Note: Product model requires 'description' field, map from incoming 'description' or 'marketing_description'
                description_value = product_data.get("description", product_data.get("marketing_description", ""))
                product_fields = {
                    "product_name": product_data.get("product_name", ""),
                    "sku": product_data.get("sku", ""),
                    "description": description_value,  # Required field
                    "category": product_data.get("category", ""),
                    "sub_category": product_data.get("sub_category", ""),
                    "marketing_description": description_value,  # Also set for backward compat
                    "detailed_spec_description": product_data.get("detailed_spec_description", ""),
                    "image_url": product_data.get("image_url", ""),
                    "image_description": product_data.get("image_description", ""),
                    "model": product_data.get("model", ""),
                    "tags": product_data.get("tags", ""),
                    "price": product_data.get("price", 0.0),
                }
                
                product = Product(**product_fields)
                await cosmos_service.upsert_product(product)
                
                results.append({
                    "sku": sku,
                    "product_name": product_name,
                    "status": "loaded"
                })
                loaded_count += 1
                logger.info(f"Loaded product: {product_name} ({sku})")
                
            except Exception as e:
                logger.error(f"Failed to load product {sku}: {e}")
                results.append({
                    "sku": sku,
                    "product_name": product_name,
                    "status": "failed",
                    "error": str(e)
                })
                failed_count += 1
        
        response = {
            "success": failed_count == 0,
            "loaded": loaded_count,
            "failed": failed_count,
            "results": results
        }
        
        if clear_existing:
            response["deleted"] = deleted_count
        
        return jsonify(response)
        
    except Exception as e:
        logger.exception(f"Error in load_sample_data: {e}")
        return jsonify({
            "error": "Internal server error",
            "message": str(e)
        }), 500


# ==================== Create Search Index Endpoint ====================

@admin_bp.route("/create-search-index", methods=["POST"])
async def create_search_index():
    """
    Create or update the Azure AI Search index with products from Cosmos DB.
    
    Request body (optional):
    {
        "index_name": "products",  // Optional: defaults to "products"
        "reindex_all": true        // Optional: re-index all products
    }
    
    Returns:
    {
        "success": true,
        "indexed": 16,
        "failed": 0,
        "index_name": "products",
        "results": [
            {"sku": "CP-0001", "product_name": "Snow Veil", "status": "indexed"},
            ...
        ]
    }
    """
    if not verify_admin_api_key():
        return unauthorized_response()
    
    try:
        # Import search-related dependencies
        from azure.core.credentials import AzureKeyCredential
        from azure.identity import DefaultAzureCredential
        from azure.search.documents import SearchClient
        from azure.search.documents.indexes import SearchIndexClient
        from azure.search.documents.indexes.models import (
            HnswAlgorithmConfiguration,
            SearchField,
            SearchFieldDataType,
            SearchIndex,
            SearchableField,
            SemanticConfiguration,
            SemanticField,
            SemanticPrioritizedFields,
            SemanticSearch,
            SimpleField,
            VectorSearch,
            VectorSearchProfile,
        )
        
        data = await request.get_json() or {}
        index_name = data.get("index_name", app_settings.search.products_index if app_settings.search else "products")
        
        search_endpoint = app_settings.search.endpoint if app_settings.search else None
        if not search_endpoint:
            return jsonify({
                "error": "Search service not configured",
                "message": "AZURE_AI_SEARCH_ENDPOINT environment variable not set"
            }), 500
        
        # Get credential - try API key first, then RBAC
        admin_key = app_settings.search.admin_key if app_settings.search else None
        if admin_key:
            credential = AzureKeyCredential(admin_key)
            logger.info("Using API key authentication for search")
        else:
            credential = DefaultAzureCredential()
            logger.info("Using RBAC authentication for search")
        
        # Create index client
        index_client = SearchIndexClient(endpoint=search_endpoint, credential=credential)
        
        # Define index schema
        fields = [
            SimpleField(name="id", type=SearchFieldDataType.String, key=True, filterable=True),
            SearchableField(name="product_name", type=SearchFieldDataType.String, filterable=True, sortable=True),
            SearchableField(name="sku", type=SearchFieldDataType.String, filterable=True),
            SearchableField(name="model", type=SearchFieldDataType.String, filterable=True),
            SearchableField(name="category", type=SearchFieldDataType.String, filterable=True, facetable=True),
            SearchableField(name="sub_category", type=SearchFieldDataType.String, filterable=True, facetable=True),
            SearchableField(name="marketing_description", type=SearchFieldDataType.String),
            SearchableField(name="detailed_spec_description", type=SearchFieldDataType.String),
            SearchableField(name="image_description", type=SearchFieldDataType.String),
            SearchableField(name="combined_text", type=SearchFieldDataType.String),
            SearchField(
                name="content_vector",
                type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
                searchable=True,
                vector_search_dimensions=1536,
                vector_search_profile_name="product-vector-profile"
            )
        ]
        
        vector_search = VectorSearch(
            algorithms=[HnswAlgorithmConfiguration(name="hnsw-algorithm")],
            profiles=[VectorSearchProfile(name="product-vector-profile", algorithm_configuration_name="hnsw-algorithm")]
        )
        
        semantic_config = SemanticConfiguration(
            name="product-semantic-config",
            prioritized_fields=SemanticPrioritizedFields(
                title_field=SemanticField(field_name="product_name"),
                content_fields=[
                    SemanticField(field_name="marketing_description"),
                    SemanticField(field_name="detailed_spec_description"),
                    SemanticField(field_name="image_description"),
                    SemanticField(field_name="combined_text")
                ],
                keywords_fields=[
                    SemanticField(field_name="category"),
                    SemanticField(field_name="sub_category"),
                    SemanticField(field_name="sku")
                ]
            )
        )
        
        index = SearchIndex(
            name=index_name,
            fields=fields,
            vector_search=vector_search,
            semantic_search=SemanticSearch(configurations=[semantic_config])
        )
        
        # Create or update index
        logger.info(f"Creating/updating search index: {index_name}")
        index_client.create_or_update_index(index)
        logger.info("Search index created/updated successfully")
        
        # Get products from Cosmos DB
        cosmos_service = await get_cosmos_service()
        products = await cosmos_service.get_all_products(limit=1000)
        logger.info(f"Found {len(products)} products to index")
        
        if not products:
            return jsonify({
                "success": True,
                "indexed": 0,
                "failed": 0,
                "index_name": index_name,
                "message": "No products found to index",
                "results": []
            })
        
        # Prepare documents for indexing
        documents = []
        results = []
        
        for product in products:
            p = product.model_dump()
            doc_id = p.get('sku', '').lower().replace("-", "_").replace(" ", "_") or p.get('id', 'unknown')
            
            combined_text = f"""
            {p.get('product_name', '')}
            Category: {p.get('category', '')} - {p.get('sub_category', '')}
            SKU: {p.get('sku', '')} | Model: {p.get('model', '')}
            Marketing: {p.get('marketing_description', '')}
            Specifications: {p.get('detailed_spec_description', '')}
            Visual: {p.get('image_description', '')}
            """
            
            documents.append({
                "id": doc_id,
                "product_name": p.get("product_name", ""),
                "sku": p.get("sku", ""),
                "model": p.get("model", ""),
                "category": p.get("category", ""),
                "sub_category": p.get("sub_category", ""),
                "marketing_description": p.get("marketing_description", ""),
                "detailed_spec_description": p.get("detailed_spec_description", ""),
                "image_description": p.get("image_description", ""),
                "combined_text": combined_text.strip(),
                "content_vector": [0.0] * 1536  # Placeholder vector
            })
            
            results.append({
                "sku": p.get("sku", ""),
                "product_name": p.get("product_name", ""),
                "status": "pending"
            })
        
        # Upload documents to search index
        search_client = SearchClient(endpoint=search_endpoint, index_name=index_name, credential=credential)
        
        try:
            upload_result = search_client.upload_documents(documents)
            
            indexed_count = 0
            failed_count = 0
            
            for i, r in enumerate(upload_result):
                if r.succeeded:
                    results[i]["status"] = "indexed"
                    indexed_count += 1
                else:
                    results[i]["status"] = "failed"
                    results[i]["error"] = str(r.error_message) if hasattr(r, 'error_message') else "Unknown error"
                    failed_count += 1
            
            logger.info(f"Indexed {indexed_count} products, {failed_count} failed")
            
            return jsonify({
                "success": failed_count == 0,
                "indexed": indexed_count,
                "failed": failed_count,
                "index_name": index_name,
                "results": results
            })
            
        except Exception as e:
            logger.exception(f"Failed to index documents: {e}")
            return jsonify({
                "error": "Failed to index documents",
                "message": str(e)
            }), 500
        
    except Exception as e:
        logger.exception(f"Error in create_search_index: {e}")
        return jsonify({
            "error": "Internal server error",
            "message": str(e)
        }), 500


# ==================== Health Check for Admin API ====================

@admin_bp.route("/health", methods=["GET"])
async def admin_health():
    """
    Health check for admin API.
    
    Does not require authentication - used to verify the admin API is available.
    """
    return jsonify({
        "status": "healthy",
        "api_key_required": bool(ADMIN_API_KEY),
        "timestamp": datetime.now(timezone.utc).isoformat()
    })
