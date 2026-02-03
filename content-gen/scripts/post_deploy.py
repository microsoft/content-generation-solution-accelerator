#!/usr/bin/env python3
"""
Post-Deployment Script for Content Generation Solution Accelerator.

This unified script handles all post-deployment tasks by calling admin APIs
that run inside the VNet (bypassing firewall restrictions):
1. Upload product images via /api/admin/upload-images
2. Load sample product data via /api/admin/load-sample-data
3. Create and populate Azure AI Search index via /api/admin/create-search-index
4. Run application health tests

The admin APIs run inside the ACI container which has private endpoint access
to Blob Storage, Cosmos DB, and Azure AI Search - eliminating the need to
modify firewall rules.

Usage:
    python post_deploy.py [options]

    Reads resource names from azd environment variables by default.
    Can override with explicit arguments if needed.

Options:
    --resource-group, -g    Resource group name (or use RESOURCE_GROUP_NAME env var)
    --app-name              App Service name (or use APP_SERVICE_NAME env var)
    --storage-account       Storage account name (or use AZURE_BLOB_ACCOUNT_NAME env var)
    --cosmos-account        Cosmos DB account name (or use COSMOSDB_ACCOUNT_NAME env var)
    --search-service        AI Search service name (or use AI_SEARCH_SERVICE_NAME env var)
    --api-key               Admin API key (or use ADMIN_API_KEY env var)
    --skip-images           Skip uploading images
    --skip-data             Skip loading sample data
    --skip-index            Skip creating search index
    --skip-tests            Skip application tests
    --dry-run               Show what would be done without executing
"""

import argparse
import asyncio
import base64
import json
import os
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, List, Dict, Any

try:
    import httpx
except ModuleNotFoundError as exc:
    missing = getattr(exc, "name", "<unknown>")
    print("\nERROR: Missing Python dependency: %s\n" % missing)
    print("Install post-deploy dependencies first, e.g.:")
    print("  python -m pip install httpx")
    sys.exit(2)


@dataclass
class ResourceConfig:
    """Configuration for Azure resources."""
    resource_group: str
    app_service: str
    app_url: str
    api_key: str = ""
    storage_account: str = ""  # Only needed for reference, not direct access
    cosmos_account: str = ""   # Only needed for reference, not direct access
    search_service: str = ""   # Only needed for reference, not direct access
    container_name: str = "product-images"


class Colors:
    """ANSI color codes for terminal output."""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    END = '\033[0m'


def print_header(text: str):
    """Print a section header."""
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'=' * 70}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}{text}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'=' * 70}{Colors.END}\n")


def print_step(text: str):
    """Print a step indicator."""
    print(f"{Colors.BLUE}→ {text}{Colors.END}")


def print_success(text: str):
    """Print a success message."""
    print(f"{Colors.GREEN}✓ {text}{Colors.END}")


def print_error(text: str):
    """Print an error message."""
    print(f"{Colors.RED}✗ {text}{Colors.END}")


def print_warning(text: str):
    """Print a warning message."""
    print(f"{Colors.YELLOW}⚠ {text}{Colors.END}")


def discover_resources(resource_group: str, app_name: str, storage_account: str, cosmos_account: str, search_service: str, api_key: str = "") -> ResourceConfig:
    """Build resource configuration from provided values (no Azure CLI required)."""
    print_step("Configuring Azure resources...")
    
    # Build App URL from app name
    app_url = f"https://{app_name}.azurewebsites.net"
    
    config = ResourceConfig(
        resource_group=resource_group,
        app_service=app_name,
        app_url=app_url,
        api_key=api_key,
        storage_account=storage_account,
        cosmos_account=cosmos_account,
        search_service=search_service
    )
    
    print(f"  App Service:     {config.app_service}")
    print(f"  App URL:         {config.app_url}")
    print(f"  Storage Account: {config.storage_account}")
    print(f"  Cosmos DB:       {config.cosmos_account}")
    print(f"  AI Search:       {config.search_service}")
    print(f"  API Key:         {'***' if config.api_key else '(not set - development mode)'}")
    
    return config


def get_api_headers(config: ResourceConfig) -> Dict[str, str]:
    """Get headers for admin API requests."""
    headers = {"Content-Type": "application/json"}
    if config.api_key:
        headers["X-Admin-API-Key"] = config.api_key
    return headers


async def check_admin_api_health(config: ResourceConfig) -> bool:
    """Check if the admin API is available."""
    print_step("Checking admin API health...")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.get(f"{config.app_url}/api/admin/health")
            if response.status_code == 200:
                data = response.json()
                print_success(f"Admin API healthy (API key required: {data.get('api_key_required', False)})")
                return True
            else:
                print_error(f"Admin API returned {response.status_code}")
                return False
        except Exception as e:
            print_error(f"Failed to reach admin API: {e}")
            return False


async def upload_images(config: ResourceConfig, dry_run: bool = False) -> int:
    """Upload product images via admin API."""
    print_header("Uploading Product Images via API")
    
    images_folder = Path(__file__).parent / "images"
    if not images_folder.exists():
        print_error(f"Images folder not found: {images_folder}")
        return 0
    
    image_files = (
        list(images_folder.glob("*.jpg")) +
        list(images_folder.glob("*.JPG")) +
        list(images_folder.glob("*.png")) +
        list(images_folder.glob("*.PNG"))
    )
    
    if not image_files:
        print_warning("No image files found")
        return 0
    
    print(f"Found {len(image_files)} image files")
    
    if dry_run:
        print_warning("DRY RUN: Would upload images via API")
        for img in sorted(image_files):
            print(f"  - {img.name}")
        return len(image_files)
    
    # Upload images one at a time
    uploaded_count = 0
    
    async with httpx.AsyncClient(timeout=120.0) as client:  # 2 minute timeout per image
        for image_path in sorted(image_files):
            content_type = "image/png" if image_path.suffix.lower() == ".png" else "image/jpeg"
            
            with open(image_path, "rb") as f:
                image_bytes = f.read()
            
            image_data = {
                "filename": image_path.name,
                "content_type": content_type,
                "data": base64.b64encode(image_bytes).decode("utf-8")
            }
            
            try:
                response = await client.post(
                    f"{config.app_url}/api/admin/upload-images",
                    headers=get_api_headers(config),
                    json={"images": [image_data]}
                )
                
                if response.status_code == 401:
                    print_error("Unauthorized - check your ADMIN_API_KEY")
                    return uploaded_count
                
                if response.status_code == 200:
                    uploaded_count += 1
                else:
                    print_error(f"{image_path.name}: API returned {response.status_code}")
                    
            except Exception as e:
                print_error(f"{image_path.name}: {e}")
    
    print(f"\nUploaded {uploaded_count}/{len(image_files)} images")
    return uploaded_count


async def load_sample_data(config: ResourceConfig, dry_run: bool = False) -> int:
    """Load sample product data via admin API."""
    print_header("Loading Sample Product Data via API")
    
    # Sample products (Contoso Paints) - image URLs use proxy path
    sample_products = [
        {"product_name": "Snow Veil", "description": "A crisp white with a hint of warmth — perfect for open, modern interiors.", "tags": "soft white, airy, minimal, fresh", "price": 59.95, "sku": "CP-0001", "image_url": f"https://{config.storage_account}.blob.core.windows.net/product-images/SnowVeil.png", "category": "Paint"},
        {"product_name": "Porcelain Mist", "description": "A gentle off-white that softens spaces with a cozy, inviting glow.", "tags": "warm neutral, beige, cozy, calm", "price": 59.95, "sku": "CP-0002", "image_url": f"https://{config.storage_account}.blob.core.windows.net/product-images/PorcelainMist.png", "category": "Paint"},
        {"product_name": "Stone Dusk", "description": "A balanced mix of gray and beige, ideal for grounding a room without heaviness.", "tags": "greige, muted, balanced, modern", "price": 59.95, "sku": "CP-0003", "image_url": f"https://{config.storage_account}.blob.core.windows.net/product-images/StoneDusk.png", "category": "Paint"},
        {"product_name": "Fog Harbor", "description": "A moody gray with blue undertones that feels sleek and contemporary.", "tags": "cool gray, stormy, industrial, sleek", "price": 59.95, "sku": "CP-0004", "image_url": f"https://{config.storage_account}.blob.core.windows.net/product-images/FogHarbor.png", "category": "Paint"},
        {"product_name": "Graphite Fade", "description": "A dark graphite shade that adds weight and sophistication to feature walls.", "tags": "charcoal, deep gray, moody, bold", "price": 59.95, "sku": "CP-0005", "image_url": f"https://{config.storage_account}.blob.core.windows.net/product-images/GraphiteFade.png", "category": "Paint"},
        {"product_name": "Obsidian Pearl", "description": "A rich black that creates contrast and drama while staying refined.", "tags": "black, matte, dramatic, luxe", "price": 59.95, "sku": "CP-0006", "image_url": f"https://{config.storage_account}.blob.core.windows.net/product-images/ObsidianPearl.png", "category": "Paint"},
        {"product_name": "Steel Sky", "description": "A mid-tone slate blue that feels steady, grounded, and architectural.", "tags": "slate, bluish gray, urban, cool", "price": 59.95, "sku": "CP-0007", "image_url": f"https://{config.storage_account}.blob.core.windows.net/product-images/SteelSky.png", "category": "Paint"},
        {"product_name": "Blue Ash", "description": "A softened navy with gray undertones — stylish but not overpowering.", "tags": "midnight, muted navy, grounding, refined", "price": 59.95, "sku": "CP-0008", "image_url": f"https://{config.storage_account}.blob.core.windows.net/product-images/BlueAsh.png", "category": "Paint"},
        {"product_name": "Cloud Drift", "description": "An ethereal off-white with subtle gray undertones that evokes soft, drifting clouds.", "tags": "cloud white, soft gray, peaceful, ethereal, airy", "price": 59.95, "sku": "CP-0009", "image_url": f"https://{config.storage_account}.blob.core.windows.net/product-images/CloudDrift.png", "category": "Paint"},
        {"product_name": "Silver Shore", "description": "A frosty gray with subtle silver hints — sharp, bright, and clean.", "tags": "cool gray, icy, clean, modern", "price": 59.95, "sku": "CP-0010", "image_url": f"https://{config.storage_account}.blob.core.windows.net/product-images/SilverShore.png", "category": "Paint"},
        {"product_name": "Seafoam Light", "description": "A soft seafoam tone that feels breezy and coastal without being too bold.", "tags": "pale green, misty, fresh, coastal", "price": 59.95, "sku": "CP-0011", "image_url": f"https://{config.storage_account}.blob.core.windows.net/product-images/SeafoamLight.png", "category": "Paint"},
        {"product_name": "Quiet Moss", "description": "A soft moss green with sage undertones that adds organic calm to any interior palette.", "tags": "moss green, sage, organic, muted, calming", "price": 59.95, "sku": "CP-0012", "image_url": f"https://{config.storage_account}.blob.core.windows.net/product-images/QuietMoss.png", "category": "Paint"},
        {"product_name": "Olive Stone", "description": "A grounded olive shade that pairs well with natural textures like wood and linen.", "tags": "earthy, muted green, natural, rustic", "price": 59.95, "sku": "CP-0013", "image_url": f"https://{config.storage_account}.blob.core.windows.net/product-images/OliveStone.png", "category": "Paint"},
        {"product_name": "Verdant Haze", "description": "A muted teal that blends serenity with just enough depth for modern accents.", "tags": "soft teal, subdued, calming, serene", "price": 59.95, "sku": "CP-0014", "image_url": f"https://{config.storage_account}.blob.core.windows.net/product-images/VerdantHaze.png", "category": "Paint"},
        {"product_name": "Glacier Tint", "description": "A barely-there aqua that brings a refreshing, clean lift to light spaces.", "tags": "pale aqua, refreshing, crisp, airy", "price": 59.95, "sku": "CP-0015", "image_url": f"https://{config.storage_account}.blob.core.windows.net/product-images/GlacierTint.png", "category": "Paint"},
        {"product_name": "Pine Shadow", "description": "A deep forest green with pine undertones that anchors a room with natural richness.", "tags": "dark green, forest, pine, earthy, grounding, natural", "price": 59.95, "sku": "CP-0016", "image_url": f"https://{config.storage_account}.blob.core.windows.net/product-images/PineShadow.png", "category": "Paint"},
    ]
    
    print(f"Sample products: {len(sample_products)} Contoso Paints items")
    
    if dry_run:
        print_warning("DRY RUN: Would load products via API")
        for p in sample_products:
            print(f"  - {p['product_name']} ({p['sku']})")
        return len(sample_products)
    
    # Call admin API
    print_step("Calling /api/admin/load-sample-data...")
    
    async with httpx.AsyncClient(timeout=120.0) as client:
        try:
            response = await client.post(
                f"{config.app_url}/api/admin/load-sample-data",
                headers=get_api_headers(config),
                json={
                    "products": sample_products,
                    "clear_existing": True
                }
            )
            
            if response.status_code == 401:
                print_error("Unauthorized - check your ADMIN_API_KEY")
                return 0
            
            if response.status_code != 200:
                print_error(f"API returned {response.status_code}: {response.text[:500]}")
                return 0
            
            result = response.json()
            loaded = result.get("loaded", 0)
            failed = result.get("failed", 0)
            deleted = result.get("deleted", 0)
            
            if deleted > 0:
                print(f"  Deleted {deleted} existing products")
            
            for r in result.get("results", []):
                if r.get("status") == "loaded":
                    print_success(f"{r['product_name']} ({r['sku']})")
                else:
                    print_error(f"{r['product_name']}: {r.get('error', 'Unknown error')}")
            
            print(f"\nLoaded {loaded}/{len(sample_products)} products ({failed} failed)")
            return loaded
            
        except Exception as e:
            print_error(f"API call failed: {e}")
            return 0


async def create_search_index(config: ResourceConfig, dry_run: bool = False) -> int:
    """Create and populate the search index via admin API."""
    print_header("Creating Search Index via API")
    
    if dry_run:
        print_warning("DRY RUN: Would create search index via API")
        return 0
    
    # Call admin API
    print_step("Calling /api/admin/create-search-index...")
    
    async with httpx.AsyncClient(timeout=180.0) as client:  # 3 minute timeout
        try:
            response = await client.post(
                f"{config.app_url}/api/admin/create-search-index",
                headers=get_api_headers(config),
                json={"reindex_all": True}
            )
            
            if response.status_code == 401:
                print_error("Unauthorized - check your ADMIN_API_KEY")
                return 0
            
            if response.status_code != 200:
                print_error(f"API returned {response.status_code}: {response.text[:500]}")
                return 0
            
            result = response.json()
            indexed = result.get("indexed", 0)
            failed = result.get("failed", 0)
            index_name = result.get("index_name", "products")
            
            print(f"  Index name: {index_name}")
            
            for r in result.get("results", []):
                if r.get("status") == "indexed":
                    print_success(f"{r['product_name']} ({r['sku']})")
                else:
                    print_error(f"{r['product_name']}: {r.get('error', 'Unknown error')}")
            
            print(f"\nIndexed {indexed} products ({failed} failed)")
            return indexed
            
        except Exception as e:
            print_error(f"API call failed: {e}")
            return 0


async def run_application_tests(config: ResourceConfig, dry_run: bool = False) -> Dict[str, bool]:
    """Run application health tests."""
    print_header("Running Application Tests")
    
    if dry_run:
        print_warning("DRY RUN: Would run application tests")
        return {}
    
    app_url = config.app_url
    print(f"App URL: {app_url}")
    print()
    
    results = {}
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Test 1: Frontend
        print_step("Testing Frontend (GET /)")
        try:
            response = await client.get(f"{app_url}/")
            if response.status_code == 200 and "<!DOCTYPE html>" in response.text:
                print_success("Frontend serving HTML")
                results["frontend"] = True
            else:
                print_error(f"Unexpected response: {response.status_code}")
                results["frontend"] = False
        except Exception as e:
            print_error(f"Failed: {e}")
            results["frontend"] = False
        
        # Test 2: Health endpoint
        print_step("Testing Health (GET /api/health)")
        try:
            response = await client.get(f"{app_url}/api/health")
            if response.status_code == 200:
                print_success(f"Health OK: {response.json()}")
                results["health"] = True
            else:
                print_warning(f"Health returned {response.status_code}")
                results["health"] = False
        except Exception as e:
            print_warning(f"Health check failed: {e}")
            results["health"] = False
        
        # Test 3: Brief Parsing (POST /api/brief/parse)
        print_step("Testing Brief Parsing (POST /api/brief/parse)")
        try:
            response = await client.post(
                f"{app_url}/api/brief/parse",
                json={"brief_text": "Create an ad for calm interior paint for homeowners."},
                headers={"Content-Type": "application/json"}
            )
            if response.status_code == 200:
                data = response.json()
                if "brief" in data:
                    print_success(f"Brief parsed: {data['brief'].get('overview', '')[:60]}...")
                    results["brief_parse"] = True
                else:
                    print_error(f"Unexpected response: {data}")
                    results["brief_parse"] = False
            else:
                print_error(f"Failed: {response.status_code} - {response.text[:200]}")
                results["brief_parse"] = False
        except Exception as e:
            print_error(f"Failed: {e}")
            results["brief_parse"] = False
        
        # Test 4: Product Search (GET /api/products)
        print_step("Testing Product Search (GET /api/products?search=blue)")
        try:
            response = await client.get(f"{app_url}/api/products?search=blue&limit=3")
            if response.status_code == 200:
                data = response.json()
                count = data.get("count", 0)
                products = data.get("products", [])
                if count > 0:
                    print_success(f"Found {count} products: {[p['product_name'] for p in products]}")
                    results["product_search"] = True
                else:
                    print_warning("No products found (search index may need time)")
                    results["product_search"] = False
            else:
                print_error(f"Failed: {response.status_code}")
                results["product_search"] = False
        except Exception as e:
            print_error(f"Failed: {e}")
            results["product_search"] = False
        
        # Test 5: Product List (GET /api/products)
        print_step("Testing Product List (GET /api/products)")
        try:
            response = await client.get(f"{app_url}/api/products?limit=5")
            if response.status_code == 200:
                data = response.json()
                count = data.get("count", 0)
                print_success(f"Listed {count} products")
                results["product_list"] = True
            else:
                print_error(f"Failed: {response.status_code}")
                results["product_list"] = False
        except Exception as e:
            print_error(f"Failed: {e}")
            results["product_list"] = False
    
    # Summary
    print()
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    if passed == total:
        print_success(f"All {total} tests passed!")
    else:
        print_warning(f"{passed}/{total} tests passed")
    
    return results


def print_summary(
    images_uploaded: int,
    products_loaded: int,
    products_indexed: int,
    test_results: Dict[str, bool]
):
    """Print final summary."""
    print_header("Post-Deployment Summary")
    
    print(f"  Images Uploaded:    {images_uploaded}")
    print(f"  Products Loaded:    {products_loaded}")
    print(f"  Products Indexed:   {products_indexed}")
    
    if test_results:
        print()
        print("  Application Tests:")
        for test, passed in test_results.items():
            status = f"{Colors.GREEN}PASS{Colors.END}" if passed else f"{Colors.RED}FAIL{Colors.END}"
            print(f"    {test}: {status}")
    
    print()


async def main():
    parser = argparse.ArgumentParser(
        description="Post-deployment script for Content Generation Solution Accelerator",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("-g", "--resource-group", help="Azure resource group name (reads from RESOURCE_GROUP_NAME if not provided)")
    parser.add_argument("--app-name", help="App Service name (reads from APP_SERVICE_NAME if not provided)")
    parser.add_argument("--storage-account", help="Storage account name (reads from AZURE_BLOB_ACCOUNT_NAME if not provided)")
    parser.add_argument("--cosmos-account", help="Cosmos DB account name (reads from COSMOSDB_ACCOUNT_NAME if not provided)")
    parser.add_argument("--search-service", help="AI Search service name (reads from AI_SEARCH_SERVICE_NAME if not provided)")
    parser.add_argument("--api-key", help="Admin API key (or set ADMIN_API_KEY env var)")
    parser.add_argument("--skip-images", action="store_true", help="Skip uploading images")
    parser.add_argument("--skip-data", action="store_true", help="Skip loading sample data")
    parser.add_argument("--skip-index", action="store_true", help="Skip creating search index")
    parser.add_argument("--skip-tests", action="store_true", help="Skip application tests")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be done")
    
    args = parser.parse_args()
    
    # Get values from args or environment variables (args take precedence)
    resource_group = args.resource_group or os.environ.get("RESOURCE_GROUP_NAME", "")
    app_name = args.app_name or os.environ.get("APP_SERVICE_NAME", "")
    storage_account = args.storage_account or os.environ.get("AZURE_BLOB_ACCOUNT_NAME", "")
    cosmos_account = args.cosmos_account or os.environ.get("COSMOSDB_ACCOUNT_NAME", "")
    search_service = args.search_service or os.environ.get("AI_SEARCH_SERVICE_NAME", "")
    api_key = args.api_key or os.environ.get("ADMIN_API_KEY", "")
    
    # Validate required values are present
    if not resource_group or not app_name or not storage_account or not cosmos_account or not search_service:
        print_error("Missing required resource names. Provide via arguments or set environment variables: RESOURCE_GROUP_NAME (--resource-group), APP_SERVICE_NAME (--app-name), AZURE_BLOB_ACCOUNT_NAME (--storage-account), COSMOSDB_ACCOUNT_NAME (--cosmos-account), AI_SEARCH_SERVICE_NAME (--search-service)")
        sys.exit(1)
    
    print_header("Content Generation Solution Accelerator - Post Deployment")
    print(f"Resource Group: {resource_group}")
    print(f"Dry Run: {args.dry_run}")
    print()
    
    # Configure resources
    config = discover_resources(resource_group, app_name, storage_account, cosmos_account, search_service, api_key)
    
    # Check admin API health first
    if not args.dry_run:
        if not await check_admin_api_health(config):
            print_error("Admin API not available. Make sure the app is deployed and running.")
            print("You can check the app at: " + config.app_url)
            sys.exit(1)
    
    images_uploaded = 0
    products_loaded = 0
    products_indexed = 0
    test_results = {}
    
    try:
        # Upload images via API
        if not args.skip_images:
            images_uploaded = await upload_images(config, dry_run=args.dry_run)
        
        # Load sample data via API
        if not args.skip_data:
            products_loaded = await load_sample_data(config, dry_run=args.dry_run)
        
        # Create search index via API
        if not args.skip_index:
            products_indexed = await create_search_index(config, dry_run=args.dry_run)
        
        # Run application tests
        if not args.skip_tests:
            test_results = await run_application_tests(config, dry_run=args.dry_run)
        
    except Exception as e:
        print_error(f"Error during post-deployment: {e}")
        raise
    
    # Print summary
    print_summary(images_uploaded, products_loaded, products_indexed, test_results)


if __name__ == "__main__":
    asyncio.run(main())
