/**
 * Message utilities — ChatMessage factory and formatting helpers.
 *
 * Replaces duplicated `msg()` helpers in useChatOrchestrator and
 * useConversationActions with a single, tested source of truth.
 */
import { v4 as uuidv4 } from 'uuid';
import type { ChatMessage } from '../types';

/**
 * Create a `ChatMessage` literal with a fresh UUID and ISO timestamp.
 */
export function createMessage(
  role: 'user' | 'assistant',
  content: string,
  agent?: string,
): ChatMessage {
  return {
    id: uuidv4(),
    role,
    content,
    agent,
    timestamp: new Date().toISOString(),
  };
}

/**
 * Shorthand for creating an assistant error message.
 * Consolidates the repeated `createMessage('assistant', errorText)` pattern
 * used in error catch blocks across multiple hooks.
 */
export function createErrorMessage(content: string): ChatMessage {
  return createMessage('assistant', content);
}
