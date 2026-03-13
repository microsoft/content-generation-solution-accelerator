/**
 * Content parsing utilities — raw API response → typed domain objects.
 *
 * Centralizes the duplicated `textContent` string-to-object parsing,
 * image URL resolution (blob rewriting, base64 fallback), and the
 * `GeneratedContent` assembly that was copy-pasted across
 * useContentGeneration, useConversationActions, and useChatOrchestrator.
 */
import type { GeneratedContent } from '../types';

/* ------------------------------------------------------------------ */
/*  Internal helpers (not exported — reduces public API surface)       */
/* ------------------------------------------------------------------ */

/**
 * Rewrite Azure Blob Storage URLs to the application's proxy endpoint
 * so the browser can fetch images without CORS issues.
 */
function rewriteBlobUrl(url: string): string {
  if (!url.includes('blob.core.windows.net')) return url;
  const parts = url.split('/');
  const filename = parts[parts.length - 1];
  const convId = parts[parts.length - 2];
  return `/api/images/${convId}/${filename}`;
}

/* ------------------------------------------------------------------ */
/*  Parsing helpers (module-internal — not re-exported)                */
/* ------------------------------------------------------------------ */

/**
 * Parse `text_content` which may arrive as a JSON string or an object.
 * Returns an object with known fields, or `undefined` if unusable.
 */
function parseTextContent(
  raw: unknown,
): { headline?: string; body?: string; cta_text?: string; tagline?: string } | undefined {
  let textContent = raw;

  if (typeof textContent === 'string') {
    try {
      textContent = JSON.parse(textContent);
    } catch {
      // Not valid JSON — treat as unusable
      return undefined;
    }
  }

  if (typeof textContent !== 'object' || textContent === null) return undefined;

  const tc = textContent as Record<string, unknown>;
  return {
    headline: tc.headline as string | undefined,
    body: tc.body as string | undefined,
    cta_text: (tc.cta_text ?? tc.cta) as string | undefined,
    tagline: tc.tagline as string | undefined,
  };
}

/**
 * Resolve the best available image URL from a raw API response.
 *
 * Priority: explicit `image_url` (with blob rewrite) → base64 data URI.
 * Pass `rewriteBlobs: true` (default) when restoring from a saved
 * conversation; `false` when the response just came from the live API.
 */
function resolveImageUrl(
  raw: { image_url?: string; image_base64?: string },
  rewriteBlobs = false,
): string | undefined {
  let url = raw.image_url;
  if (url && rewriteBlobs) {
    url = rewriteBlobUrl(url);
  }
  if (url) return url;
  if (raw.image_base64) return `data:image/png;base64,${raw.image_base64}`;
  return undefined;
}

/**
 * Build a fully-typed `GeneratedContent` from an arbitrary raw API payload.
 *
 * @param raw         The parsed JSON object from the backend.
 * @param rewriteBlobs  Pass `true` when restoring from a saved conversation
 *                      so Azure Blob URLs get proxied.
 */
// eslint-disable-next-line @typescript-eslint/no-explicit-any
export function buildGeneratedContent(raw: any, rewriteBlobs = false): GeneratedContent {
  const textContent = parseTextContent(raw.text_content);
  const imageUrl = resolveImageUrl(raw, rewriteBlobs);

  return {
    text_content: textContent,
    image_content:
      imageUrl || raw.image_prompt
        ? {
            image_url: imageUrl,
            prompt_used: raw.image_prompt,
            alt_text: raw.image_revised_prompt || 'Generated marketing image',
          }
        : undefined,
    violations: raw.violations || [],
    requires_modification: raw.requires_modification || false,
    error: raw.error,
    image_error: raw.image_error,
    text_error: raw.text_error,
  };
}
