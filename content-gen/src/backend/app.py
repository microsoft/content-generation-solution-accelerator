"""
Content Generation Solution Accelerator - Main Application Entry Point.

This is the main Quart application that provides the REST API for the
Intelligent Content Generation Accelerator.
"""

import asyncio
import json
import logging
import os
import uuid
from datetime import datetime, timezone
from typing import Dict, Any

from quart import Quart, request, jsonify, Response
from quart_cors import cors

from settings import app_settings
from models import CreativeBrief, Product
from orchestrator import get_orchestrator
from services.cosmos_service import get_cosmos_service
from services.blob_service import get_blob_service
from api.admin import admin_bp

# In-memory task storage for generation tasks
# In production, this should be replaced with Redis or similar
_generation_tasks: Dict[str, Dict[str, Any]] = {}

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Create Quart app
app = Quart(__name__)
app = cors(app, allow_origin="*")

# Register blueprints
app.register_blueprint(admin_bp)


# ==================== Authentication Helper ====================

def get_authenticated_user():
    """
    Get the authenticated user from EasyAuth headers.
    
    In production (with App Service Auth), the X-Ms-Client-Principal-Id header
    contains the user's ID. In development mode, returns "anonymous".
    """
    user_principal_id = request.headers.get("X-Ms-Client-Principal-Id", "")
    user_name = request.headers.get("X-Ms-Client-Principal-Name", "")
    auth_provider = request.headers.get("X-Ms-Client-Principal-Idp", "")
    
    return {
        "user_principal_id": user_principal_id or "anonymous",
        "user_name": user_name or "",
        "auth_provider": auth_provider or "",
        "is_authenticated": bool(user_principal_id)
    }


# ==================== Health Check ====================

@app.route("/health", methods=["GET"])
@app.route("/api/health", methods=["GET"])
async def health_check():
    """Health check endpoint."""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": "1.0.0"
    })


# ==================== User Info Endpoint ====================

@app.route("/api/user", methods=["GET"])
async def get_current_user():
    """
    Get the current authenticated user info.
    
    Returns user details from EasyAuth headers, or empty values if not authenticated.
    """
    user = get_authenticated_user()
    return jsonify(user)


# ==================== Chat Endpoints ====================

@app.route("/api/chat", methods=["POST"])
async def chat():
    """
    Process a chat message through the agent orchestration.
    
    Request body:
    {
        "message": "User's message",
        "conversation_id": "optional-uuid",
        "user_id": "user identifier"
    }
    
    Returns streaming response with agent responses.
    """
    data = await request.get_json()
    
    message = data.get("message", "")
    conversation_id = data.get("conversation_id") or str(uuid.uuid4())
    user_id = data.get("user_id", "anonymous")
    
    if not message:
        return jsonify({"error": "Message is required"}), 400
    
    orchestrator = get_orchestrator()
    
    # Try to save to CosmosDB but don't fail if it's unavailable
    try:
        cosmos_service = await get_cosmos_service()
        await cosmos_service.add_message_to_conversation(
            conversation_id=conversation_id,
            user_id=user_id,
            message={
                "role": "user",
                "content": message,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )
    except Exception as e:
        logger.warning(f"Failed to save message to CosmosDB: {e}")
    
    async def generate():
        """Stream responses from the orchestrator."""
        try:
            async for response in orchestrator.process_message(
                message=message,
                conversation_id=conversation_id
            ):
                yield f"data: {json.dumps(response)}\n\n"
                
                # Save assistant responses when final OR when requiring user input
                if response.get("is_final") or response.get("requires_user_input"):
                    if response.get("content"):
                        try:
                            cosmos_service = await get_cosmos_service()
                            await cosmos_service.add_message_to_conversation(
                                conversation_id=conversation_id,
                                user_id=user_id,
                                message={
                                    "role": "assistant",
                                    "content": response.get("content", ""),
                                    "agent": response.get("agent", ""),
                                    "timestamp": datetime.now(timezone.utc).isoformat()
                                }
                            )
                        except Exception as e:
                            logger.warning(f"Failed to save response to CosmosDB: {e}")
        except Exception as e:
            logger.exception(f"Error in orchestrator: {e}")
            yield f"data: {json.dumps({'type': 'error', 'content': str(e), 'is_final': True})}\n\n"
        
        yield "data: [DONE]\n\n"
    
    return Response(
        generate(),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no"
        }
    )


# ==================== Creative Brief Endpoints ====================

@app.route("/api/brief/parse", methods=["POST"])
async def parse_brief():
    """
    Parse a free-text creative brief into structured format.
    If critical information is missing, return clarifying questions.
    
    Request body:
    {
        "brief_text": "Free-form creative brief text",
        "conversation_id": "optional-uuid",
        "user_id": "user identifier"
    }
    
    Returns:
        Structured CreativeBrief JSON for user confirmation,
        or clarifying questions if info is missing.
    """
    data = await request.get_json()
    brief_text = data.get("brief_text", "")
    conversation_id = data.get("conversation_id") or str(uuid.uuid4())
    user_id = data.get("user_id", "anonymous")
    
    if not brief_text:
        return jsonify({"error": "Brief text is required"}), 400
    
    # Save the user's brief text as a message to CosmosDB
    try:
        cosmos_service = await get_cosmos_service()
        await cosmos_service.add_message_to_conversation(
            conversation_id=conversation_id,
            user_id=user_id,
            message={
                "role": "user",
                "content": brief_text,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )
    except Exception as e:
        logger.warning(f"Failed to save brief message to CosmosDB: {e}")
    
    orchestrator = get_orchestrator()
    parsed_brief, clarifying_questions, rai_blocked = await orchestrator.parse_brief(brief_text)
    
    # Check if request was blocked due to harmful content
    if rai_blocked:
        # Save the refusal as assistant response
        try:
            cosmos_service = await get_cosmos_service()
            await cosmos_service.add_message_to_conversation(
                conversation_id=conversation_id,
                user_id=user_id,
                message={
                    "role": "assistant",
                    "content": clarifying_questions,  # This is the refusal message
                    "agent": "ContentSafety",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            )
        except Exception as e:
            logger.warning(f"Failed to save RAI response to CosmosDB: {e}")
        
        return jsonify({
            "rai_blocked": True,
            "requires_clarification": False,
            "requires_confirmation": False,
            "conversation_id": conversation_id,
            "message": clarifying_questions
        })
    
    # Check if we need clarifying questions
    if clarifying_questions:
        # Save the clarifying questions as assistant response
        try:
            cosmos_service = await get_cosmos_service()
            await cosmos_service.add_message_to_conversation(
                conversation_id=conversation_id,
                user_id=user_id,
                message={
                    "role": "assistant",
                    "content": clarifying_questions,
                    "agent": "PlanningAgent",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            )
        except Exception as e:
            logger.warning(f"Failed to save clarifying questions to CosmosDB: {e}")
        
        return jsonify({
            "brief": parsed_brief.model_dump(),
            "requires_clarification": True,
            "requires_confirmation": False,
            "clarifying_questions": clarifying_questions,
            "conversation_id": conversation_id,
            "message": clarifying_questions
        })
    
    # Save the assistant's parsing response
    try:
        cosmos_service = await get_cosmos_service()
        await cosmos_service.add_message_to_conversation(
            conversation_id=conversation_id,
            user_id=user_id,
            message={
                "role": "assistant",
                "content": "I've parsed your creative brief. Please review and confirm the details before we proceed.",
                "agent": "PlanningAgent",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )
    except Exception as e:
        logger.warning(f"Failed to save parsing response to CosmosDB: {e}")
    
    return jsonify({
        "brief": parsed_brief.model_dump(),
        "requires_clarification": False,
        "requires_confirmation": True,
        "conversation_id": conversation_id,
        "message": "Please review and confirm the parsed creative brief"
    })


@app.route("/api/brief/confirm", methods=["POST"])
async def confirm_brief():
    """
    Confirm or modify a parsed creative brief.
    
    Request body:
    {
        "brief": { ... CreativeBrief fields ... },
        "conversation_id": "optional-uuid",
        "user_id": "user identifier"
    }
    
    Returns:
        Confirmation status and next steps.
    """
    data = await request.get_json()
    brief_data = data.get("brief", {})
    conversation_id = data.get("conversation_id") or str(uuid.uuid4())
    user_id = data.get("user_id", "anonymous")
    
    try:
        brief = CreativeBrief(**brief_data)
    except Exception as e:
        return jsonify({"error": f"Invalid brief format: {str(e)}"}), 400
    
    # Try to save the confirmed brief to CosmosDB, preserving existing messages
    try:
        cosmos_service = await get_cosmos_service()
        
        # Get existing conversation to preserve messages
        existing = await cosmos_service.get_conversation(conversation_id, user_id)
        existing_messages = existing.get("messages", []) if existing else []
        
        # Add confirmation message
        existing_messages.append({
            "role": "assistant",
            "content": "Great! Your creative brief has been confirmed. Now you can select products to feature and generate content.",
            "agent": "TriageAgent",
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
        await cosmos_service.save_conversation(
            conversation_id=conversation_id,
            user_id=user_id,
            messages=existing_messages,
            brief=brief,
            metadata={"status": "brief_confirmed"}
        )
    except Exception as e:
        logger.warning(f"Failed to save brief to CosmosDB: {e}")
    
    return jsonify({
        "status": "confirmed",
        "conversation_id": conversation_id,
        "brief": brief.model_dump(),
        "message": "Brief confirmed. Ready for content generation."
    })


# ==================== Product Selection Endpoints ====================

@app.route("/api/products/select", methods=["POST"])
async def select_products():
    """
    Select or modify products via natural language.
    
    Request body:
    {
        "request": "User's natural language request",
        "current_products": [ ... currently selected products ... ],
        "conversation_id": "optional-uuid",
        "user_id": "user identifier"
    }
    
    Returns:
        Selected products and assistant message.
    """
    data = await request.get_json()
    
    request_text = data.get("request", "")
    current_products = data.get("current_products", [])
    conversation_id = data.get("conversation_id") or str(uuid.uuid4())
    user_id = data.get("user_id", "anonymous")
    
    if not request_text:
        return jsonify({"error": "Request text is required"}), 400
    
    # Save user message
    try:
        cosmos_service = await get_cosmos_service()
        await cosmos_service.add_message_to_conversation(
            conversation_id=conversation_id,
            user_id=user_id,
            message={
                "role": "user",
                "content": request_text,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )
    except Exception as e:
        logger.warning(f"Failed to save product selection request to CosmosDB: {e}")
    
    # Get available products from catalog
    try:
        cosmos_service = await get_cosmos_service()
        all_products = await cosmos_service.get_all_products(limit=50)
        # Use mode='json' to ensure datetime objects are serialized to strings
        available_products = [p.model_dump(mode='json') for p in all_products]
        
        # Convert blob URLs to proxy URLs
        for p in available_products:
            if p.get("image_url"):
                original_url = p["image_url"]
                filename = original_url.split("/")[-1] if "/" in original_url else original_url
                p["image_url"] = f"/api/product-images/{filename}"
    except Exception as e:
        logger.warning(f"Failed to get products from CosmosDB: {e}")
        available_products = []
    
    # Use orchestrator to process the selection request
    orchestrator = get_orchestrator()
    result = await orchestrator.select_products(
        request_text=request_text,
        current_products=current_products,
        available_products=available_products
    )
    
    # Save assistant response
    try:
        cosmos_service = await get_cosmos_service()
        await cosmos_service.add_message_to_conversation(
            conversation_id=conversation_id,
            user_id=user_id,
            message={
                "role": "assistant",
                "content": result.get("message", "Products updated."),
                "agent": "ProductAgent",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )
    except Exception as e:
        logger.warning(f"Failed to save product selection response to CosmosDB: {e}")
    
    return jsonify({
        "products": result.get("products", []),
        "action": result.get("action", "search"),
        "message": result.get("message", "Products selected."),
        "conversation_id": conversation_id
    })


# ==================== Content Generation Endpoints ====================

async def _run_generation_task(task_id: str, brief: CreativeBrief, products_data: list, 
                                generate_images: bool, conversation_id: str, user_id: str):
    """Background task to run content generation."""
    try:
        logger.info(f"Starting background generation task {task_id}")
        _generation_tasks[task_id]["status"] = "running"
        _generation_tasks[task_id]["started_at"] = datetime.now(timezone.utc).isoformat()
        
        orchestrator = get_orchestrator()
        response = await orchestrator.generate_content(
            brief=brief,
            products=products_data,
            generate_images=generate_images
        )
        
        logger.info(f"Generation task {task_id} completed. Response keys: {list(response.keys()) if response else 'None'}")
        
        # Handle image URL from orchestrator's blob save
        if response.get("image_blob_url"):
            blob_url = response["image_blob_url"]
            logger.info(f"Image already saved to blob by orchestrator: {blob_url}")
            parts = blob_url.split("/")
            filename = parts[-1]
            conv_folder = parts[-2]
            response["image_url"] = f"/api/images/{conv_folder}/{filename}"
            response["image_blob_url"] = blob_url  # Keep the original blob URL in response
            logger.info(f"Converted to proxy URL: {response['image_url']}")
        elif response.get("image_base64"):
            # Fallback: save to blob
            try:
                blob_service = await get_blob_service()
                blob_url = await blob_service.save_generated_image(
                    conversation_id=conversation_id,
                    image_base64=response["image_base64"]
                )
                if blob_url:
                    parts = blob_url.split("/")
                    filename = parts[-1]
                    response["image_url"] = f"/api/images/{conversation_id}/{filename}"
                    response["image_blob_url"] = blob_url  # Include the original blob URL
                    del response["image_base64"]
            except Exception as e:
                logger.warning(f"Failed to save image to blob: {e}")
        
        # Save to CosmosDB
        try:
            cosmos_service = await get_cosmos_service()
            
            await cosmos_service.add_message_to_conversation(
                conversation_id=conversation_id,
                user_id=user_id,
                message={
                    "role": "assistant",
                    "content": "Content generated successfully.",
                    "agent": "ContentAgent",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            )
            
            generated_content_to_save = {
                "text_content": response.get("text_content"),
                "image_url": response.get("image_url"),
                "image_prompt": response.get("image_prompt"),
                "image_revised_prompt": response.get("image_revised_prompt"),
                "violations": response.get("violations", []),
                "requires_modification": response.get("requires_modification", False),
                "selected_products": products_data  # Save the selected products
            }
            await cosmos_service.save_generated_content(
                conversation_id=conversation_id,
                user_id=user_id,
                generated_content=generated_content_to_save
            )
        except Exception as e:
            logger.warning(f"Failed to save generated content to CosmosDB: {e}")
        
        _generation_tasks[task_id]["status"] = "completed"
        _generation_tasks[task_id]["result"] = response
        _generation_tasks[task_id]["completed_at"] = datetime.now(timezone.utc).isoformat()
        logger.info(f"Task {task_id} marked as completed")
        
    except Exception as e:
        logger.exception(f"Generation task {task_id} failed: {e}")
        _generation_tasks[task_id]["status"] = "failed"
        _generation_tasks[task_id]["error"] = str(e)
        _generation_tasks[task_id]["completed_at"] = datetime.now(timezone.utc).isoformat()


@app.route("/api/generate/start", methods=["POST"])
async def start_generation():
    """
    Start content generation and return immediately with a task ID.
    Client should poll /api/generate/status/<task_id> for results.
    
    Request body:
    {
        "brief": { ... CreativeBrief fields ... },
        "products": [ ... Product list (optional) ... ],
        "generate_images": true/false,
        "conversation_id": "uuid"
    }
    
    Returns:
    {
        "task_id": "uuid",
        "status": "pending",
        "message": "Generation started"
    }
    """
    global _generation_tasks
    
    data = await request.get_json()
    
    brief_data = data.get("brief", {})
    products_data = data.get("products", [])
    generate_images = data.get("generate_images", True)
    conversation_id = data.get("conversation_id") or str(uuid.uuid4())
    user_id = data.get("user_id", "anonymous")
    
    try:
        brief = CreativeBrief(**brief_data)
    except Exception as e:
        return jsonify({"error": f"Invalid brief format: {str(e)}"}), 400
    
    # Create task ID
    task_id = str(uuid.uuid4())
    
    # Initialize task state
    _generation_tasks[task_id] = {
        "status": "pending",
        "conversation_id": conversation_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "result": None,
        "error": None
    }
    
    # Save user request
    try:
        cosmos_service = await get_cosmos_service()
        product_names = [p.get("product_name", "product") for p in products_data[:3]]
        await cosmos_service.add_message_to_conversation(
            conversation_id=conversation_id,
            user_id=user_id,
            message={
                "role": "user",
                "content": f"Generate content for: {', '.join(product_names) if product_names else 'the campaign'}",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )
    except Exception as e:
        logger.warning(f"Failed to save generation request to CosmosDB: {e}")
    
    # Start background task
    asyncio.create_task(_run_generation_task(
        task_id=task_id,
        brief=brief,
        products_data=products_data,
        generate_images=generate_images,
        conversation_id=conversation_id,
        user_id=user_id
    ))
    
    logger.info(f"Started generation task {task_id} for conversation {conversation_id}")
    
    return jsonify({
        "task_id": task_id,
        "status": "pending",
        "conversation_id": conversation_id,
        "message": "Generation started. Poll /api/generate/status/{task_id} for results."
    })


@app.route("/api/generate/status/<task_id>", methods=["GET"])
async def get_generation_status(task_id: str):
    """
    Get the status of a generation task.
    
    Returns:
    {
        "task_id": "uuid",
        "status": "pending" | "running" | "completed" | "failed",
        "result": { ... generated content ... } (if completed),
        "error": "error message" (if failed)
    }
    """
    global _generation_tasks
    
    if task_id not in _generation_tasks:
        return jsonify({"error": "Task not found"}), 404
    
    task = _generation_tasks[task_id]
    
    response = {
        "task_id": task_id,
        "status": task["status"],
        "conversation_id": task.get("conversation_id"),
        "created_at": task.get("created_at"),
    }
    
    if task["status"] == "completed":
        response["result"] = task["result"]
        response["completed_at"] = task.get("completed_at")
    elif task["status"] == "failed":
        response["error"] = task["error"]
        response["completed_at"] = task.get("completed_at")
    elif task["status"] == "running":
        response["started_at"] = task.get("started_at")
        response["message"] = "Generation in progress..."
    
    return jsonify(response)


@app.route("/api/generate", methods=["POST"])
async def generate_content():
    """
    Generate content from a confirmed creative brief.
    
    Request body:
    {
        "brief": { ... CreativeBrief fields ... },
        "products": [ ... Product list (optional) ... ],
        "generate_images": true/false,
        "conversation_id": "uuid"
    }
    
    Returns streaming response with generated content.
    """
    import asyncio
    
    data = await request.get_json()
    
    brief_data = data.get("brief", {})
    products_data = data.get("products", [])
    generate_images = data.get("generate_images", True)
    conversation_id = data.get("conversation_id") or str(uuid.uuid4())
    user_id = data.get("user_id", "anonymous")
    
    try:
        brief = CreativeBrief(**brief_data)
    except Exception as e:
        return jsonify({"error": f"Invalid brief format: {str(e)}"}), 400
    
    # Save user request for content generation
    try:
        cosmos_service = await get_cosmos_service()
        product_names = [p.get("product_name", "product") for p in products_data[:3]]
        await cosmos_service.add_message_to_conversation(
            conversation_id=conversation_id,
            user_id=user_id,
            message={
                "role": "user",
                "content": f"Generate content for: {', '.join(product_names) if product_names else 'the campaign'}",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )
    except Exception as e:
        logger.warning(f"Failed to save generation request to CosmosDB: {e}")
    
    orchestrator = get_orchestrator()
    
    async def generate():
        """Stream content generation responses with keepalive heartbeats."""
        logger.info(f"Starting SSE generator for conversation {conversation_id}")
        generation_task = None
        
        try:
            # Create a task for the long-running generation
            generation_task = asyncio.create_task(
                orchestrator.generate_content(
                    brief=brief,
                    products=products_data,
                    generate_images=generate_images
                )
            )
            logger.info("Generation task created")
            
            # Send keepalive heartbeats every 15 seconds while generation is running
            heartbeat_count = 0
            
            while not generation_task.done():
                # Check every 0.5 seconds (faster response to completion)
                for _ in range(30):  # 30 * 0.5s = 15 seconds
                    if generation_task.done():
                        logger.info("Task completed during heartbeat wait (iteration)")
                        break
                    await asyncio.sleep(0.5)
                
                if not generation_task.done():
                    heartbeat_count += 1
                    logger.info(f"Sending heartbeat {heartbeat_count}")
                    yield f"data: {json.dumps({'type': 'heartbeat', 'count': heartbeat_count, 'message': 'Generating content...'})}\n\n"
            
            logger.info(f"Generation task completed after {heartbeat_count} heartbeats")
        except asyncio.CancelledError:
            logger.warning(f"SSE generator cancelled for conversation {conversation_id}")
            if generation_task and not generation_task.done():
                generation_task.cancel()
            raise
        except GeneratorExit:
            logger.warning(f"SSE generator closed by client for conversation {conversation_id}")
            if generation_task and not generation_task.done():
                generation_task.cancel()
            return
        except Exception as e:
            logger.exception(f"Unexpected error in SSE generator heartbeat loop: {e}")
            if generation_task and not generation_task.done():
                generation_task.cancel()
            raise
        
        # Get the result
        try:
            response = generation_task.result()
            logger.info(f"Generation complete. Response keys: {list(response.keys()) if response else 'None'}")
            has_image_base64 = bool(response.get("image_base64")) if response else False
            has_image_blob = bool(response.get("image_blob_url")) if response else False
            image_size = len(response.get("image_base64", "")) if response else 0
            logger.info(f"Has image_base64: {has_image_base64}, has_image_blob_url: {has_image_blob}, base64_size: {image_size} bytes")
            
            # Handle image URL from orchestrator's blob save
            if response.get("image_blob_url"):
                blob_url = response["image_blob_url"]
                logger.info(f"Image already saved to blob by orchestrator: {blob_url}")
                # Convert blob URL to proxy URL for frontend access
                parts = blob_url.split("/")
                filename = parts[-1]  # e.g., "20251202222126.png"
                conv_folder = parts[-2]  # e.g., "gen_20251209225131"
                response["image_url"] = f"/api/images/{conv_folder}/{filename}"
                del response["image_blob_url"]
                logger.info(f"Converted to proxy URL: {response['image_url']}")
            # Fallback: save image_base64 to blob if orchestrator didn't do it
            elif response.get("image_base64"):
                try:
                    logger.info("Getting blob service for fallback save...")
                    blob_service = await get_blob_service()
                    logger.info(f"Saving image to blob storage for conversation {conversation_id}...")
                    blob_url = await blob_service.save_generated_image(
                        conversation_id=conversation_id,
                        image_base64=response["image_base64"]
                    )
                    logger.info(f"Blob save returned: {blob_url}")
                    if blob_url:
                        parts = blob_url.split("/")
                        filename = parts[-1]
                        response["image_url"] = f"/api/images/{conversation_id}/{filename}"
                        del response["image_base64"]
                        logger.info(f"Image saved to blob storage, URL: {response['image_url']}")
                except Exception as e:
                    logger.warning(f"Failed to save image to blob storage: {e}", exc_info=True)
                    # Keep image_base64 in response as fallback if blob storage fails
            else:
                logger.info("No image in response")
            
            # Save generated content to conversation
            try:
                cosmos_service = await get_cosmos_service()
                
                # Save the message
                await cosmos_service.add_message_to_conversation(
                    conversation_id=conversation_id,
                    user_id=user_id,
                    message={
                        "role": "assistant",
                        "content": "Content generated successfully.",
                        "agent": "ContentAgent",
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    }
                )
                
                # Save the full generated content for restoration
                # Note: image_base64 is NOT saved to CosmosDB as it exceeds document size limits
                # Images will only persist if blob storage is working
                generated_content_to_save = {
                    "text_content": response.get("text_content"),
                    "image_url": response.get("image_url"),
                    "image_prompt": response.get("image_prompt"),
                    "image_revised_prompt": response.get("image_revised_prompt"),
                    "violations": response.get("violations", []),
                    "requires_modification": response.get("requires_modification", False),
                    "selected_products": products_data  # Save the selected products
                }
                await cosmos_service.save_generated_content(
                    conversation_id=conversation_id,
                    user_id=user_id,
                    generated_content=generated_content_to_save
                )
            except Exception as e:
                logger.warning(f"Failed to save generated content to CosmosDB: {e}")
            
            # Format response to match what frontend expects
            yield f"data: {json.dumps({'type': 'agent_response', 'content': json.dumps(response), 'is_final': True})}\n\n"
        except Exception as e:
            logger.exception(f"Error generating content: {e}")
            yield f"data: {json.dumps({'type': 'error', 'content': str(e), 'is_final': True})}\n\n"
        
        yield "data: [DONE]\n\n"
    
    return Response(
        generate(),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream; charset=utf-8",
        }
    )


@app.route("/api/regenerate", methods=["POST"])
async def regenerate_content():
    """
    Regenerate image based on user modification request.
    
    This endpoint is called when the user wants to modify the generated image
    after initial content generation (e.g., "show a kitchen instead of dining room").
    
    Request body:
    {
        "modification_request": "User's modification request",
        "brief": { ... CreativeBrief fields ... },
        "products": [ ... Product list ... ],
        "previous_image_prompt": "Previous image prompt (optional)",
        "conversation_id": "uuid"
    }
    
    Returns regenerated image with the modification applied.
    """
    import asyncio
    
    data = await request.get_json()
    
    modification_request = data.get("modification_request", "")
    brief_data = data.get("brief", {})
    products_data = data.get("products", [])
    previous_image_prompt = data.get("previous_image_prompt")
    conversation_id = data.get("conversation_id") or str(uuid.uuid4())
    user_id = data.get("user_id", "anonymous")
    
    if not modification_request:
        return jsonify({"error": "modification_request is required"}), 400
    
    try:
        brief = CreativeBrief(**brief_data)
    except Exception as e:
        return jsonify({"error": f"Invalid brief format: {str(e)}"}), 400
    
    # Save user request for regeneration
    try:
        cosmos_service = await get_cosmos_service()
        await cosmos_service.add_message_to_conversation(
            conversation_id=conversation_id,
            user_id=user_id,
            message={
                "role": "user",
                "content": f"Modify image: {modification_request}",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )
    except Exception as e:
        logger.warning(f"Failed to save regeneration request to CosmosDB: {e}")
    
    orchestrator = get_orchestrator()
    
    async def generate():
        """Stream regeneration responses with keepalive heartbeats."""
        logger.info(f"Starting image regeneration for conversation {conversation_id}")
        regeneration_task = None
        
        try:
            # Create a task for the regeneration
            regeneration_task = asyncio.create_task(
                orchestrator.regenerate_image(
                    modification_request=modification_request,
                    brief=brief,
                    products=products_data,
                    previous_image_prompt=previous_image_prompt
                )
            )
            
            # Send keepalive heartbeats while regeneration is running
            heartbeat_count = 0
            while not regeneration_task.done():
                for _ in range(30):  # 15 seconds
                    if regeneration_task.done():
                        break
                    await asyncio.sleep(0.5)
                
                if not regeneration_task.done():
                    heartbeat_count += 1
                    yield f"data: {json.dumps({'type': 'heartbeat', 'count': heartbeat_count, 'message': 'Regenerating image...'})}\n\n"
            
        except asyncio.CancelledError:
            logger.warning(f"Regeneration cancelled for conversation {conversation_id}")
            if regeneration_task and not regeneration_task.done():
                regeneration_task.cancel()
            raise
        except GeneratorExit:
            logger.warning(f"Regeneration closed by client for conversation {conversation_id}")
            if regeneration_task and not regeneration_task.done():
                regeneration_task.cancel()
            return
        
        # Get the result
        try:
            response = regeneration_task.result()
            logger.info(f"Regeneration complete. Response keys: {list(response.keys()) if response else 'None'}")
            
            # Check for RAI block
            if response.get("rai_blocked"):
                yield f"data: {json.dumps({'type': 'error', 'content': response.get('error', 'Request blocked by content safety'), 'rai_blocked': True, 'is_final': True})}\n\n"
                yield "data: [DONE]\n\n"
                return
            
            # Handle image URL from orchestrator's blob save
            if response.get("image_blob_url"):
                blob_url = response["image_blob_url"]
                parts = blob_url.split("/")
                filename = parts[-1]
                conv_folder = parts[-2]
                response["image_url"] = f"/api/images/{conv_folder}/{filename}"
                del response["image_blob_url"]
            elif response.get("image_base64"):
                # Save to blob storage
                try:
                    blob_service = await get_blob_service()
                    blob_url = await blob_service.save_generated_image(
                        conversation_id=conversation_id,
                        image_base64=response["image_base64"]
                    )
                    if blob_url:
                        parts = blob_url.split("/")
                        filename = parts[-1]
                        response["image_url"] = f"/api/images/{conversation_id}/{filename}"
                        del response["image_base64"]
                except Exception as e:
                    logger.warning(f"Failed to save regenerated image to blob: {e}")
            
            # Save assistant response
            try:
                cosmos_service = await get_cosmos_service()
                await cosmos_service.add_message_to_conversation(
                    conversation_id=conversation_id,
                    user_id=user_id,
                    message={
                        "role": "assistant",
                        "content": response.get("message", "Image regenerated based on your request."),
                        "agent": "ImageAgent",
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    }
                )
            except Exception as e:
                logger.warning(f"Failed to save regeneration response to CosmosDB: {e}")
            
            yield f"data: {json.dumps({'type': 'agent_response', 'content': json.dumps(response), 'is_final': True})}\n\n"
        except Exception as e:
            logger.exception(f"Error in regeneration: {e}")
            yield f"data: {json.dumps({'type': 'error', 'content': str(e), 'is_final': True})}\n\n"
        
        yield "data: [DONE]\n\n"
    
    return Response(
        generate(),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream; charset=utf-8",
        }
    )


# ==================== Image Proxy Endpoints ====================

@app.route("/api/images/<conversation_id>/<filename>", methods=["GET"])
async def proxy_generated_image(conversation_id: str, filename: str):
    """
    Proxy generated images from blob storage.
    This allows the frontend to access images without exposing blob storage credentials.
    """
    try:
        blob_service = await get_blob_service()
        await blob_service.initialize()
        
        blob_name = f"{conversation_id}/{filename}"
        blob_client = blob_service._generated_images_container.get_blob_client(blob_name)
        
        # Download the blob
        download = await blob_client.download_blob()
        image_data = await download.readall()
        
        # Determine content type from filename
        content_type = "image/png" if filename.endswith(".png") else "image/jpeg"
        
        return Response(
            image_data,
            mimetype=content_type,
            headers={
                "Cache-Control": "public, max-age=86400",  # Cache for 24 hours
            }
        )
    except Exception as e:
        logger.exception(f"Error proxying image: {e}")
        return jsonify({"error": "Image not found"}), 404


@app.route("/api/product-images/<filename>", methods=["GET"])
async def proxy_product_image(filename: str):
    """
    Proxy product images from blob storage.
    This allows the frontend to access product images via private endpoint.
    The filename should match the blob name (e.g., SnowVeil.png).
    """
    try:
        blob_service = await get_blob_service()
        await blob_service.initialize()
        
        blob_client = blob_service._product_images_container.get_blob_client(filename)
        
        # Get blob properties for ETag/Last-Modified
        properties = await blob_client.get_blob_properties()
        etag = properties.etag.strip('"') if properties.etag else None
        last_modified = properties.last_modified
        
        # Check If-None-Match header for cache validation
        if_none_match = request.headers.get("If-None-Match")
        if if_none_match and etag and if_none_match.strip('"') == etag:
            return Response(status=304)  # Not Modified
        
        # Download the blob
        download = await blob_client.download_blob()
        image_data = await download.readall()
        
        # Determine content type from filename
        content_type = "image/png" if filename.endswith(".png") else "image/jpeg"
        
        headers = {
            "Cache-Control": "public, max-age=300, must-revalidate",  # Cache 5 min, revalidate
        }
        if etag:
            headers["ETag"] = f'"{etag}"'
        if last_modified:
            headers["Last-Modified"] = last_modified.strftime("%a, %d %b %Y %H:%M:%S GMT")
        
        return Response(
            image_data,
            mimetype=content_type,
            headers=headers
        )
    except Exception as e:
        logger.exception(f"Error proxying product image {filename}: {e}")
        return jsonify({"error": "Image not found"}), 404


# ==================== Product Endpoints ====================

@app.route("/api/products", methods=["GET"])
async def list_products():
    """
    List all products.
    
    Query params:
        category: Filter by category
        sub_category: Filter by sub-category
        search: Search term
        limit: Max number of results (default 20)
    """
    category = request.args.get("category")
    sub_category = request.args.get("sub_category")
    search = request.args.get("search")
    limit = int(request.args.get("limit", 20))
    
    cosmos_service = await get_cosmos_service()
    
    if search:
        products = await cosmos_service.search_products(search, limit)
    elif category:
        products = await cosmos_service.get_products_by_category(
            category, sub_category, limit
        )
    else:
        products = await cosmos_service.get_all_products(limit)
    
    # Convert blob URLs to proxy URLs for products with images
    product_list = []
    for p in products:
        product_dict = p.model_dump()
        # Convert direct blob URL to proxy URL
        if product_dict.get("image_url"):
            # Extract filename from URL like https://account.blob.../container/SnowVeil.png
            original_url = product_dict["image_url"]
            filename = original_url.split("/")[-1] if "/" in original_url else original_url
            product_dict["image_url"] = f"/api/product-images/{filename}"
        product_list.append(product_dict)
    
    return jsonify({
        "products": product_list,
        "count": len(product_list)
    })


@app.route("/api/products/<sku>", methods=["GET"])
async def get_product(sku: str):
    """Get a product by SKU."""
    cosmos_service = await get_cosmos_service()
    product = await cosmos_service.get_product_by_sku(sku)
    
    if not product:
        return jsonify({"error": "Product not found"}), 404
    
    product_dict = product.model_dump()
    # Convert direct blob URL to proxy URL
    if product_dict.get("image_url"):
        original_url = product_dict["image_url"]
        filename = original_url.split("/")[-1] if "/" in original_url else original_url
        product_dict["image_url"] = f"/api/product-images/{filename}"
    
    return jsonify(product_dict)


@app.route("/api/products", methods=["POST"])
async def create_product():
    """
    Create or update a product.
    
    Request body:
    {
        "product_name": "...",
        "category": "...",
        "sub_category": "...",
        "marketing_description": "...",
        "detailed_spec_description": "...",
        "sku": "...",
        "model": "..."
    }
    """
    data = await request.get_json()
    
    try:
        product = Product(**data)
    except Exception as e:
        return jsonify({"error": f"Invalid product format: {str(e)}"}), 400
    
    cosmos_service = await get_cosmos_service()
    saved_product = await cosmos_service.upsert_product(product)
    
    return jsonify(saved_product.model_dump()), 201


@app.route("/api/products/<sku>/image", methods=["POST"])
async def upload_product_image(sku: str):
    """
    Upload an image for a product.
    
    The image will be stored and a description will be auto-generated
    using GPT-5 Vision.
    
    Request: multipart/form-data with 'image' file
    """
    cosmos_service = await get_cosmos_service()
    product = await cosmos_service.get_product_by_sku(sku)
    
    if not product:
        return jsonify({"error": "Product not found"}), 404
    
    files = await request.files
    if "image" not in files:
        return jsonify({"error": "No image file provided"}), 400
    
    image_file = files["image"]
    image_data = image_file.read()
    content_type = image_file.content_type or "image/jpeg"
    
    blob_service = await get_blob_service()
    image_url, description = await blob_service.upload_product_image(
        sku=sku,
        image_data=image_data,
        content_type=content_type
    )
    
    # Update product with image info
    product.image_url = image_url
    product.image_description = description
    await cosmos_service.upsert_product(product)
    
    return jsonify({
        "image_url": image_url,
        "image_description": description,
        "message": "Image uploaded and description generated"
    })


# ==================== Conversation Endpoints ====================

@app.route("/api/conversations", methods=["GET"])
async def list_conversations():
    """
    List conversations for a user.
    
    Uses authenticated user from EasyAuth headers. In development mode
    (when not authenticated), uses "anonymous" as user_id.
    
    Query params:
        limit: Max number of results (default 20)
    """
    auth_user = get_authenticated_user()
    user_id = auth_user["user_principal_id"]
    
    limit = int(request.args.get("limit", 20))
    
    cosmos_service = await get_cosmos_service()
    conversations = await cosmos_service.get_user_conversations(user_id, limit)
    
    return jsonify({
        "conversations": conversations,
        "count": len(conversations)
    })


@app.route("/api/conversations/<conversation_id>", methods=["GET"])
async def get_conversation(conversation_id: str):
    """
    Get a specific conversation.
    
    Uses authenticated user from EasyAuth headers.
    """
    auth_user = get_authenticated_user()
    user_id = auth_user["user_principal_id"]
    
    cosmos_service = await get_cosmos_service()
    conversation = await cosmos_service.get_conversation(conversation_id, user_id)
    
    if not conversation:
        return jsonify({"error": "Conversation not found"}), 404
    
    return jsonify(conversation)


@app.route("/api/conversations/<conversation_id>", methods=["DELETE"])
async def delete_conversation(conversation_id: str):
    """
    Delete a specific conversation.
    
    Uses authenticated user from EasyAuth headers.
    """
    auth_user = get_authenticated_user()
    user_id = auth_user["user_principal_id"]
    
    try:
        cosmos_service = await get_cosmos_service()
        await cosmos_service.delete_conversation(conversation_id, user_id)
        return jsonify({"success": True, "message": "Conversation deleted"})
    except Exception as e:
        logger.warning(f"Failed to delete conversation: {e}")
        return jsonify({"error": "Failed to delete conversation"}), 500


@app.route("/api/conversations/<conversation_id>", methods=["PUT"])
async def update_conversation(conversation_id: str):
    """
    Update a conversation (rename).
    
    Uses authenticated user from EasyAuth headers.
    
    Request body:
    {
        "title": "New conversation title"
    }
    """
    auth_user = get_authenticated_user()
    user_id = auth_user["user_principal_id"]
    
    data = await request.get_json()
    new_title = data.get("title", "").strip()
    
    if not new_title:
        return jsonify({"error": "Title is required"}), 400
    
    try:
        cosmos_service = await get_cosmos_service()
        result = await cosmos_service.rename_conversation(conversation_id, user_id, new_title)
        if result:
            return jsonify({"success": True, "message": "Conversation renamed", "title": new_title})
        return jsonify({"error": "Conversation not found"}), 404
    except Exception as e:
        logger.warning(f"Failed to rename conversation: {e}")
        return jsonify({"error": "Failed to rename conversation"}), 500


# ==================== Brand Guidelines Endpoints ====================

@app.route("/api/brand-guidelines", methods=["GET"])
async def get_brand_guidelines():
    """Get current brand guidelines configuration."""
    return jsonify({
        "tone": app_settings.brand_guidelines.tone,
        "voice": app_settings.brand_guidelines.voice,
        "primary_color": app_settings.brand_guidelines.primary_color,
        "secondary_color": app_settings.brand_guidelines.secondary_color,
        "prohibited_words": app_settings.brand_guidelines.prohibited_words,
        "required_disclosures": app_settings.brand_guidelines.required_disclosures,
        "max_headline_length": app_settings.brand_guidelines.max_headline_length,
        "max_body_length": app_settings.brand_guidelines.max_body_length,
        "require_cta": app_settings.brand_guidelines.require_cta
    })


# ==================== UI Configuration ====================

@app.route("/api/config", methods=["GET"])
async def get_ui_config():
    """Get UI configuration including feature flags."""
    return jsonify({
        "app_name": app_settings.ui.app_name,
        "show_brand_guidelines": True,
        "enable_image_generation": app_settings.azure_openai.image_generation_enabled,
        "image_model": app_settings.azure_openai.effective_image_model if app_settings.azure_openai.image_generation_enabled else None,
        "enable_compliance_check": True,
        "max_file_size_mb": 10
    })


# ==================== Application Lifecycle ====================

@app.before_serving
async def startup():
    """Initialize services on application startup."""
    logger.info("Starting Content Generation Solution Accelerator...")
    
    # Initialize orchestrator
    get_orchestrator()
    logger.info("Orchestrator initialized with Microsoft Agent Framework")
    
    # Try to initialize services - they may fail if CosmosDB/Blob storage is not accessible
    try:
        await get_cosmos_service()
        logger.info("CosmosDB service initialized")
    except Exception as e:
        logger.warning(f"CosmosDB service initialization failed (may be firewall): {e}")
    
    try:
        await get_blob_service()
        logger.info("Blob storage service initialized")
    except Exception as e:
        logger.warning(f"Blob storage service initialization failed: {e}")
    
    logger.info("Application startup complete")


@app.after_serving
async def shutdown():
    """Cleanup on application shutdown."""
    logger.info("Shutting down Content Generation Solution Accelerator...")
    
    cosmos_service = await get_cosmos_service()
    await cosmos_service.close()
    
    blob_service = await get_blob_service()
    await blob_service.close()
    
    logger.info("Application shutdown complete")


# ==================== Error Handlers ====================

@app.errorhandler(404)
async def not_found(error):
    """Handle 404 errors."""
    return jsonify({"error": "Not found"}), 404


@app.errorhandler(500)
async def server_error(error):
    """Handle 500 errors."""
    logger.exception(f"Server error: {error}")
    return jsonify({"error": "Internal server error"}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
