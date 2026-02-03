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

const API_BASE = '/api';

/**
 * Get application configuration including feature flags
 */
export async function getAppConfig(): Promise<AppConfig> {
  const response = await fetch(`${API_BASE}/config`);

  if (!response.ok) {
    throw new Error(`Failed to get config: ${response.statusText}`);
  }

  return response.json();
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
  const response = await fetch(`${API_BASE}/brief/parse`, {
    signal,
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      brief_text: briefText,
      conversation_id: conversationId,
      user_id: userId || 'anonymous',
    }),
  });

  if (!response.ok) {
    throw new Error(`Failed to parse brief: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Confirm a parsed creative brief
 */
export async function confirmBrief(
  brief: CreativeBrief,
  conversationId?: string,
  userId?: string
): Promise<{ status: string; conversation_id: string; brief: CreativeBrief }> {
  const response = await fetch(`${API_BASE}/brief/confirm`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      brief,
      conversation_id: conversationId,
      user_id: userId || 'anonymous',
    }),
  });

  if (!response.ok) {
    throw new Error(`Failed to confirm brief: ${response.statusText}`);
  }

  return response.json();
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
  const response = await fetch(`${API_BASE}/products/select`, {
    signal,
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      request,
      current_products: currentProducts,
      conversation_id: conversationId,
      user_id: userId || 'anonymous',
    }),
  });

  if (!response.ok) {
    throw new Error(`Failed to select products: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Stream chat messages from the agent orchestration
 */
export async function* streamChat(
  message: string,
  conversationId?: string,
  userId?: string,
  signal?: AbortSignal
): AsyncGenerator<AgentResponse> {
  const response = await fetch(`${API_BASE}/chat`, {
    signal,
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      message,
      conversation_id: conversationId,
      user_id: userId || 'anonymous',
    }),
  });

  if (!response.ok) {
    throw new Error(`Chat request failed: ${response.statusText}`);
  }

  const reader = response.body?.getReader();
  if (!reader) {
    throw new Error('No response body');
  }

  const decoder = new TextDecoder();
  let buffer = '';

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split('\n\n');
    buffer = lines.pop() || '';

    for (const line of lines) {
      if (line.startsWith('data: ')) {
        const data = line.slice(6);
        if (data === '[DONE]') {
          return;
        }
        try {
          yield JSON.parse(data) as AgentResponse;
        } catch {
          console.error('Failed to parse SSE data:', data);
        }
      }
    }
  }
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
  const startResponse = await fetch(`${API_BASE}/generate/start`, {
    signal,
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      brief,
      products: products || [],
      generate_images: generateImages,
      conversation_id: conversationId,
      user_id: userId || 'anonymous',
    }),
  });

  if (!startResponse.ok) {
    throw new Error(`Content generation failed to start: ${startResponse.statusText}`);
  }

  const startData = await startResponse.json();
  const taskId = startData.task_id;
  
  console.log(`Generation started with task ID: ${taskId}`);
  
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
      const statusResponse = await fetch(`${API_BASE}/generate/status/${taskId}`, { signal });
      if (!statusResponse.ok) {
        throw new Error(`Failed to get task status: ${statusResponse.statusText}`);
      }
      
      const statusData = await statusResponse.json();
      
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
        // Determine progress stage based on elapsed time
        // Typical generation: 0-10s briefing, 10-25s copy, 25-45s image, 45-60s compliance
        const elapsedSeconds = attempts;
        let stage: number;
        let stageMessage: string;
        
        if (elapsedSeconds < 10) {
          stage = 0;
          stageMessage = 'Analyzing creative brief...';
        } else if (elapsedSeconds < 25) {
          stage = 1;
          stageMessage = 'Generating marketing copy...';
        } else if (elapsedSeconds < 35) {
          stage = 2;
          stageMessage = 'Creating image prompt...';
        } else if (elapsedSeconds < 55) {
          stage = 3;
          stageMessage = 'Generating image with AI...';
        } else if (elapsedSeconds < 70) {
          stage = 4;
          stageMessage = 'Running compliance check...';
        } else {
          stage = 5;
          stageMessage = 'Finalizing content...';
        }
        
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
      console.error(`Error polling task ${taskId}:`, error);
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
  brief: CreativeBrief,
  products?: Product[],
  previousImagePrompt?: string,
  conversationId?: string,
  userId?: string,
  signal?: AbortSignal
): AsyncGenerator<AgentResponse> {
  const response = await fetch(`${API_BASE}/regenerate`, {
    signal,
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      modification_request: modificationRequest,
      brief,
      products: products || [],
      previous_image_prompt: previousImagePrompt,
      conversation_id: conversationId,
      user_id: userId || 'anonymous',
    }),
  });

  if (!response.ok) {
    throw new Error(`Regeneration request failed: ${response.statusText}`);
  }

  const reader = response.body?.getReader();
  if (!reader) {
    throw new Error('No response body');
  }

  const decoder = new TextDecoder();
  let buffer = '';

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split('\n\n');
    buffer = lines.pop() || '';

    for (const line of lines) {
      if (line.startsWith('data: ')) {
        const data = line.slice(6);
        if (data === '[DONE]') {
          return;
        }
        try {
          yield JSON.parse(data) as AgentResponse;
        } catch {
          console.error('Failed to parse SSE data:', data);
        }
      }
    }
  }
}