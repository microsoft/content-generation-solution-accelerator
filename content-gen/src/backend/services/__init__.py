"""Services package for Content Generation Solution Accelerator."""

from services.cosmos_service import CosmosDBService, get_cosmos_service
from services.blob_service import BlobStorageService, get_blob_service

__all__ = [
    "CosmosDBService",
    "get_cosmos_service",
    "BlobStorageService",
    "get_blob_service",
]
