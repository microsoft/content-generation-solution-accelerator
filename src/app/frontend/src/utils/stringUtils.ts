/**
 * String utilities — regex escaping, name swapping, keyword matching.
 *
 * Extracts the duplicated keyword-matching pattern and the regex-escape +
 * swapName closure from useChatOrchestrator into reusable, testable functions.
 */

/**
 * Escape a string so it can be safely embedded in a `RegExp` pattern.
 * @internal — only used by `createNameSwapper` within this module.
 */
function escapeRegex(str: string): string {
  return str.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

/**
 * Create a function that replaces all case-insensitive occurrences of
 * `oldName` with `newName` in a string.
 *
 * Returns `undefined` if no swap is possible (names are the same, etc.).
 */
export function createNameSwapper(
  oldName: string | undefined,
  newName: string | undefined,
): ((text?: string) => string | undefined) | undefined {
  if (!oldName || !newName || oldName === newName) return undefined;

  const regex = new RegExp(escapeRegex(oldName), 'gi');
  return (text?: string) => {
    if (!text) return text;
    return text.replace(regex, () => newName);
  };
}

/**
 * Check whether `text` contains **any** of the given keywords
 * (case-insensitive substring match).
 *
 * Used for intent classification (brief detection, refinement detection,
 * image modification detection) repeated 3× in useChatOrchestrator.
 */
export function matchesAnyKeyword(text: string, keywords: readonly string[]): boolean {
  const lower = text.toLowerCase();
  return keywords.some((kw) => lower.includes(kw));
}
