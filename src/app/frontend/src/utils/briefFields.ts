/**
 * Brief-field metadata shared between BriefReview and ConfirmedBriefView.
 *
 * Eliminates the duplicated field-label arrays.
 */
import type { CreativeBrief } from '../types';

/**
 * Canonical map from `CreativeBrief` keys to user-friendly labels.
 * Used by BriefReview (completeness gauges) and ConfirmedBriefView.
 */
export const BRIEF_FIELD_LABELS: Record<keyof CreativeBrief, string> = {
  overview: 'Overview',
  objectives: 'Objectives',
  target_audience: 'Target Audience',
  key_message: 'Key Message',
  tone_and_style: 'Tone & Style',
  deliverable: 'Deliverable',
  timelines: 'Timelines',
  visual_guidelines: 'Visual Guidelines',
  cta: 'Call to Action',
};

/**
 * Display order for brief fields in review UIs.
 *
 * The first element in each tuple is the `CreativeBrief` key, the second
 * is the UI label (which may differ slightly from `BRIEF_FIELD_LABELS`
 * for contextual reasons, e.g. "Campaign Objective" vs "Overview").
 */
export const BRIEF_DISPLAY_ORDER: { key: keyof CreativeBrief; label: string }[] = [
  { key: 'overview', label: 'Campaign Objective' },
  { key: 'objectives', label: 'Objectives' },
  { key: 'target_audience', label: 'Target Audience' },
  { key: 'key_message', label: 'Key Message' },
  { key: 'tone_and_style', label: 'Tone & Style' },
  { key: 'visual_guidelines', label: 'Visual Guidelines' },
  { key: 'deliverable', label: 'Deliverables' },
  { key: 'timelines', label: 'Timelines' },
  { key: 'cta', label: 'Call to Action' },
];

/**
 * The canonical list of all nine brief field keys, in display order.
 */
export const BRIEF_FIELD_KEYS: (keyof CreativeBrief)[] = BRIEF_DISPLAY_ORDER.map((f) => f.key);
