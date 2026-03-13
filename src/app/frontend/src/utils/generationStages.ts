/**
 * Generation progress stage mapping.
 *
 * Pure function that converts elapsed seconds into a human-readable
 * stage label + ordinal — used by the polling loop in `streamGenerateContent`.
 */

export interface GenerationStage {
  /** Ordinal stage index (0–5) for progress indicators. */
  stage: number;
  /** Human-readable status message. */
  message: string;
}

/**
 * Map elapsed seconds to the current generation stage.
 *
 * Typical generation timeline:
 * - 0 – 10 s  → Briefing analysis
 * - 10 – 25 s → Copy generation
 * - 25 – 35 s → Image prompt creation
 * - 35 – 55 s → Image generation
 * - 55 – 70 s → Compliance check
 * - 70 s+     → Finalizing
 */
export function getGenerationStage(elapsedSeconds: number): GenerationStage {
  if (elapsedSeconds < 10) return { stage: 0, message: 'Analyzing creative brief...' };
  if (elapsedSeconds < 25) return { stage: 1, message: 'Generating marketing copy...' };
  if (elapsedSeconds < 35) return { stage: 2, message: 'Creating image prompt...' };
  if (elapsedSeconds < 55) return { stage: 3, message: 'Generating image with AI...' };
  if (elapsedSeconds < 70) return { stage: 4, message: 'Running compliance check...' };
  return { stage: 5, message: 'Finalizing content...' };
}
