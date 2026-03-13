/**
 * Detect whether an error message originates from a content-safety filter.
 */
export function isContentFilterError(errorMessage?: string): boolean {
  if (!errorMessage) return false;
  const filterPatterns = [
    'content_filter', 'ContentFilter', 'content management policy',
    'ResponsibleAI', 'responsible_ai_policy', 'content filtering',
    'filtered', 'safety system', 'self_harm', 'sexual', 'violence', 'hate',
  ];
  return filterPatterns.some((pattern) =>
    errorMessage.toLowerCase().includes(pattern.toLowerCase()),
  );
}

/**
 * Return a user-friendly title/description for a generation error.
 */
export function getErrorMessage(errorMessage?: string): { title: string; description: string } {
  if (isContentFilterError(errorMessage)) {
    return {
      title: 'Content Filtered',
      description:
        'Your request was blocked by content safety filters. Please try modifying your creative brief.',
    };
  }
  return {
    title: 'Generation Failed',
    description: errorMessage || 'An error occurred. Please try again.',
  };
}
