/**
 * Barrel export for all utility modules.
 *
 * Import everything you need from '../utils'.
 */

// Message factories & formatting
export { createMessage, createErrorMessage } from './messageUtils';

// Content parsing (raw API → typed domain objects)
export { buildGeneratedContent } from './contentParsing';

// SSE stream parser
export { parseSSEStream } from './sseParser';

// Generation progress stages
export { getGenerationStage } from './generationStages';

// Brief-field metadata
export { BRIEF_FIELD_LABELS, BRIEF_DISPLAY_ORDER, BRIEF_FIELD_KEYS } from './briefFields';

// String utilities
export { createNameSwapper, matchesAnyKeyword } from './stringUtils';

// Content error detection
export { isContentFilterError, getErrorMessage } from './contentErrors';

// Image download
export { downloadImage } from './downloadImage';

// Shared UI constants
export const AI_DISCLAIMER = 'AI-generated content may be incorrect';
