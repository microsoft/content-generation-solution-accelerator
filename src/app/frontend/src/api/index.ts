/**
 * API service for interacting with the Content Generation backend
 */

import type {
  AgentResponse,
  AppConfig,
  MessageRequest,
  MessageResponse,
} from '../types';

const API_BASE = '/api';

/**
 * Send a message or action to the /api/chat endpoint
 */
export async function sendMessage(
  request: MessageRequest,
  signal?: AbortSignal
): Promise<MessageResponse> {
  const response = await fetch(`${API_BASE}/chat`, {
    signal,
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    throw new Error(`Message request failed: ${response.statusText}`);
  }

  return response.json();
}

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
 * Request for content generation
 */
export interface GenerateRequest {
  conversation_id: string;
  user_id: string;
  brief: Record<string, unknown>;
  products: Array<Record<string, unknown>>;
  generate_images: boolean;
}

/**
 * Generate content from a confirmed brief
 */
export async function* streamGenerateContent(
  request: GenerateRequest,
  signal?: AbortSignal
): AsyncGenerator<AgentResponse> {
  // Use polling-based approach for reliability with long-running tasks
  const startResponse = await fetch(`${API_BASE}/generate/start`, {
    signal,
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      brief: request.brief,
      products: request.products || [],
      generate_images: request.generate_images,
      conversation_id: request.conversation_id,
      user_id: request.user_id || 'anonymous',
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
 * Poll for task completion using task_id
 * Used for both content generation and image regeneration
 */
export async function* pollTaskStatus(
  taskId: string,
  signal?: AbortSignal
): AsyncGenerator<AgentResponse> {
  let attempts = 0;
  const maxAttempts = 600; // 10 minutes max with 1-second polling
  const pollInterval = 1000; // 1 second
  
  while (attempts < maxAttempts) {
    if (signal?.aborted) {
      throw new DOMException('Operation cancelled by user', 'AbortError');
    }
    
    await new Promise(resolve => setTimeout(resolve, pollInterval));
    attempts++;
    
    if (signal?.aborted) {
      throw new DOMException('Operation cancelled by user', 'AbortError');
    }
    
    try {
      const statusResponse = await fetch(`${API_BASE}/generate/status/${taskId}`, { signal });
      if (!statusResponse.ok) {
        throw new Error(`Failed to get task status: ${statusResponse.statusText}`);
      }
      
      const statusData = await statusResponse.json();
      
      if (statusData.status === 'completed') {
        yield {
          type: 'agent_response',
          content: JSON.stringify(statusData.result),
          is_final: true,
        } as AgentResponse;
        return;
      } else if (statusData.status === 'failed') {
        throw new Error(statusData.error || 'Task failed');
      } else {
        // Yield heartbeat with progress
        const elapsedSeconds = attempts;
        let stageMessage: string;
        
        if (elapsedSeconds < 10) {
          stageMessage = 'Starting regeneration...';
        } else if (elapsedSeconds < 30) {
          stageMessage = 'Generating new image...';
        } else if (elapsedSeconds < 50) {
          stageMessage = 'Processing image...';
        } else {
          stageMessage = 'Finalizing...';
        }
        
        yield {
          type: 'heartbeat',
          content: stageMessage,
          elapsed: elapsedSeconds,
          is_final: false,
        } as AgentResponse;
      }
    } catch (error) {
      if (attempts >= maxAttempts) {
        throw error;
      }
    }
  }
  
  throw new Error('Task timed out after 10 minutes');
}