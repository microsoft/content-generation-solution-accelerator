/**
 * API service for interacting with the Content Generation backend
 */

import type {
  CreativeBrief,
  Product,
  AgentResponse,
  ParsedBriefResponse,
  AppConfig,
} from '../types';
import httpClient from './httpClient';
export { default as httpClient } from './httpClient';
import { getGenerationStage } from '../utils';

/** Normalize optional userId to a safe fallback. */
function normalizeUserId(userId?: string): string {
  return userId || 'anonymous';
}

/**
 * Get application configuration including feature flags
 */
export async function getAppConfig(): Promise<AppConfig> {
  return httpClient.get<AppConfig>('/config');
}

/**
 * Parse a free-text creative brief into structured format
 */
export async function parseBrief(
  briefText: string,
  conversationId?: string,
  userId?: string,
  signal?: AbortSignal
): Promise<ParsedBriefResponse> {
  return httpClient.post<ParsedBriefResponse>('/chat', {
    message: briefText,
    conversation_id: conversationId,
    user_id: normalizeUserId(userId),
  }, { signal });
}

/**
 * Confirm a parsed creative brief
 */
export async function confirmBrief(
  brief: CreativeBrief,
  conversationId?: string,
  userId?: string
): Promise<{ status: string; conversation_id: string; brief: CreativeBrief }> {
  return httpClient.post('/brief/confirm', {
    brief,
    conversation_id: conversationId,
    user_id: normalizeUserId(userId),
  });
}

/**
 * Select or modify products via natural language
 */
export async function selectProducts(
  request: string,
  currentProducts: Product[],
  conversationId?: string,
  userId?: string,
  signal?: AbortSignal
): Promise<{ products: Product[]; action: string; message: string; conversation_id: string }> {
  return httpClient.post('/chat', {
    message: request,
    current_products: currentProducts,
    conversation_id: conversationId,
    user_id: normalizeUserId(userId),
  }, { signal });
}

/**
 * Stream chat messages from the agent orchestration.
 *
 * Note: The /chat endpoint returns JSON (not SSE), so we perform a standard
 * POST request and yield the single AgentResponse result.
 */
export async function* streamChat(
  message: string,
  conversationId?: string,
  userId?: string,
  signal?: AbortSignal
): AsyncGenerator<AgentResponse> {
  const result = await httpClient.post<AgentResponse>(
    '/chat',
    {
      message,
      conversation_id: conversationId,
      user_id: normalizeUserId(userId),
    },
    { signal },
  );

  // Preserve async-iterator interface by yielding the single JSON response.
  yield result;
}

/**
 * Generate content from a confirmed brief
 */
export async function* streamGenerateContent(
  brief: CreativeBrief,
  products?: Product[],
  generateImages: boolean = true,
  conversationId?: string,
  userId?: string,
  signal?: AbortSignal
): AsyncGenerator<AgentResponse> {
  // Use polling-based approach for reliability with long-running tasks
  const startData = await httpClient.post<{ task_id: string }>('/generate/start', {
    brief,
    products: products || [],
    generate_images: generateImages,
    conversation_id: conversationId,
    user_id: normalizeUserId(userId),
  }, { signal });
  const taskId = startData.task_id;
  
  // Yield initial status
  yield {
    type: 'status',
    content: 'Generation started...',
    is_final: false,
  } as AgentResponse;
  
  // Poll for completion
  let attempts = 0;
  const maxAttempts = 600; // 10 minutes max with 1-second polling (image generation can take 3-5 min)
  const pollInterval = 1000; // 1 second
  
  while (attempts < maxAttempts) {
    // Check if cancelled before waiting
    if (signal?.aborted) {
      throw new DOMException('Generation cancelled by user', 'AbortError');
    }
    
    await new Promise(resolve => setTimeout(resolve, pollInterval));
    attempts++;
    
    // Check if cancelled after waiting
    if (signal?.aborted) {
      throw new DOMException('Generation cancelled by user', 'AbortError');
    }
    
    try {
      const statusData = await httpClient.get<{ status: string; result?: unknown; error?: string }>(
        `/generate/status/${taskId}`,
        { signal },
      );
      
      if (statusData.status === 'completed') {
        // Yield the final result
        yield {
          type: 'agent_response',
          content: JSON.stringify(statusData.result),
          is_final: true,
        } as AgentResponse;
        return;
      } else if (statusData.status === 'failed') {
        throw new Error(statusData.error || 'Generation failed');
      } else if (statusData.status === 'running') {
        const elapsedSeconds = attempts;
        const { stage, message: stageMessage } = getGenerationStage(elapsedSeconds);
        
        // Send status update every second for smoother progress
        yield {
          type: 'heartbeat',
          content: stageMessage,
          count: stage,
          elapsed: elapsedSeconds,
          is_final: false,
        } as AgentResponse;
      }
    } catch (error) {
      // Continue polling on transient errors
      if (attempts >= maxAttempts) {
        throw error;
      }
    }
  }
  
  throw new Error('Generation timed out after 10 minutes');
}
/**
 * Regenerate image with a modification request
 * Used when user wants to change the generated image after initial content generation
 */
export async function* streamRegenerateImage(
  modificationRequest: string,
  _brief: CreativeBrief,
  products?: Product[],
  _previousImagePrompt?: string,
  conversationId?: string,
  userId?: string,
  signal?: AbortSignal
): AsyncGenerator<AgentResponse> {
  // Image regeneration uses the unified /chat endpoint with MODIFY_IMAGE intent,
  // which returns a task_id for polling via /generate/status.
  const startData = await httpClient.post<{ action_type: string; data: { task_id: string; poll_url: string }; conversation_id: string }>(
    '/chat',
    {
      message: modificationRequest,
      conversation_id: conversationId,
      user_id: normalizeUserId(userId),
      selected_products: products || [],
      has_generated_content: true,
    },
    { signal },
  );

  const taskId = startData.data?.task_id;
  if (!taskId) {
    // If no task_id, the response is the final result itself
    yield { type: 'agent_response', content: JSON.stringify(startData), is_final: true } as AgentResponse;
    return;
  }

  yield { type: 'status', content: 'Regeneration started...', is_final: false } as AgentResponse;

  let attempts = 0;
  const maxAttempts = 600;
  const pollInterval = 1000;

  while (attempts < maxAttempts) {
    if (signal?.aborted) {
      throw new DOMException('Regeneration cancelled by user', 'AbortError');
    }

    await new Promise(resolve => setTimeout(resolve, pollInterval));
    attempts++;

    if (signal?.aborted) {
      throw new DOMException('Regeneration cancelled by user', 'AbortError');
    }

    const statusData = await httpClient.get<{ status: string; result?: unknown; error?: string }>(
      `/generate/status/${taskId}`,
      { signal },
    );

    if (statusData.status === 'completed') {
      yield { type: 'agent_response', content: JSON.stringify(statusData.result), is_final: true } as AgentResponse;
      return;
    } else if (statusData.status === 'failed') {
      throw new Error(statusData.error || 'Regeneration failed');
    } else {
      const { stage, message: stageMessage } = getGenerationStage(attempts);
      yield { type: 'heartbeat', content: stageMessage, count: stage, elapsed: attempts, is_final: false } as AgentResponse;
    }
  }

  throw new Error('Regeneration timed out after 10 minutes');
}