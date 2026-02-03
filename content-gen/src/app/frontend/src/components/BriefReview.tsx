import {
  Button,
  Text,
  tokens,
} from '@fluentui/react-components';
import type { CreativeBrief } from '../types';

interface BriefReviewProps {
  brief: CreativeBrief;
  onConfirm: () => void;
  onStartOver: () => void;
  isAwaitingResponse?: boolean;
}

// Mapping of field keys to user-friendly labels for the 9 key areas
const fieldLabels: Record<keyof CreativeBrief, string> = {
  overview: 'Overview',
  objectives: 'Objectives',
  target_audience: 'Target Audience',
  key_message: 'Key Message',
  tone_and_style: 'Tone and Style',
  deliverable: 'Deliverable',
  timelines: 'Timelines',
  visual_guidelines: 'Visual Guidelines',
  cta: 'Call to Action',
};

export function BriefReview({
  brief,
  onConfirm,
  onStartOver,
  isAwaitingResponse = false,
}: BriefReviewProps) {
  const allFields: (keyof CreativeBrief)[] = [
    'overview', 'objectives', 'target_audience', 'key_message', 
    'tone_and_style', 'deliverable', 'timelines', 'visual_guidelines', 'cta'
  ];
  const populatedFields = allFields.filter(key => brief[key]?.trim()).length;
  const missingFields = allFields.filter(key => !brief[key]?.trim());

  // Define the order and labels for display in the card
  const displayOrder: { key: keyof CreativeBrief; label: string }[] = [
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

  // Filter to only populated fields
  const populatedDisplayFields = displayOrder.filter(({ key }) => brief[key]?.trim());

  return (
    <div className="message assistant" style={{ 
      width: '100%',
      alignSelf: 'flex-start',
      backgroundColor: tokens.colorNeutralBackground3,
      padding: '12px 16px',
      borderRadius: '8px',
      margin: '16px 0 0 0',
    }}>
      {/* Header text */}
      <Text 
        size={300} 
        style={{ 
          display: 'block',
          marginBottom: '12px',
          color: tokens.colorNeutralForeground1,
        }}
      >
        Thanks—here's my understanding:
      </Text>
      
      {/* All Brief Fields in a single bordered card */}
      {populatedDisplayFields.length > 0 && (
        <div style={{
          padding: '16px',
          backgroundColor: tokens.colorNeutralBackground2,
          borderRadius: '8px',
          marginBottom: '16px',
          border: `1px solid ${tokens.colorNeutralStroke2}`,
        }}>
          {populatedDisplayFields.map(({ key, label }, index) => (
            <div key={key} style={{ marginBottom: index < populatedDisplayFields.length - 1 ? '12px' : '0' }}>
              <Text 
                weight="semibold" 
                size={300}
                style={{ 
                  color: tokens.colorNeutralForeground1,
                  display: 'block',
                  marginBottom: '4px',
                }}
              >
                {label}
              </Text>
              <Text size={200} style={{ color: tokens.colorNeutralForeground2, lineHeight: '1.5' }}>
                {brief[key]}
              </Text>
            </div>
          ))}
        </div>
      )}

      <div style={{
        padding: '12px 16px',
        backgroundColor: tokens.colorNeutralBackground2,
        borderRadius: '8px',
        marginBottom: '16px',
        borderLeft: `3px solid ${tokens.colorBrandBackground}`,
      }}>
        <Text size={200} style={{ color: tokens.colorNeutralForeground1, lineHeight: '1.6' }}>
          {populatedFields < 5 ? (
            <>
              I've captured <strong>{populatedFields}</strong> of 9 key areas. Would you like to add more details? 
              You are missing: <strong>{missingFields.map(f => fieldLabels[f]).join(', ')}</strong>.
              <br /><br />
              You can tell me things like:
              <ul style={{ margin: '8px 0 0 0', paddingLeft: '20px' }}>
                <li>"The target audience should be homeowners aged 35-55"</li>
                <li>"Add a timeline of 2 weeks for the campaign"</li>
                <li>"The tone should be warm and inviting"</li>
              </ul>
            </>
          ) : (
            <>
              Does this look correct? You can:
              <ul style={{ margin: '8px 0 0 0', paddingLeft: '20px' }}>
                <li><strong>Modify:</strong> "Change the target audience to young professionals"</li>
                <li><strong>Add:</strong> "Add a call to action: Shop Now"</li>
                <li><strong>Remove:</strong> "Remove the timelines section"</li>
              </ul>
              Or if everything looks good, click <strong>Confirm brief</strong> to proceed.
            </>
          )}
        </Text>
      </div>
      
      {/* Action Buttons - Matching Figma styling */}
      <div style={{ 
        display: 'flex', 
        gap: '8px',
        flexWrap: 'wrap',
      }}>
        <Button
          appearance="outline"
          onClick={onStartOver}
          size="small"
          disabled={isAwaitingResponse}
          style={{
            borderColor: tokens.colorNeutralStroke1,
            fontWeight: 600,
          }}
        >
          Start over
        </Button>
        <Button
          appearance="primary"
          onClick={onConfirm}
          size="small"
          disabled={isAwaitingResponse}
          style={{ fontWeight: 600 }}
        >
          Confirm brief
        </Button>
      </div>

      {/* AI disclaimer footer */}
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginTop: '12px',
        paddingTop: '8px',
      }}>
        <Text size={100} style={{ color: tokens.colorNeutralForeground4 }}>
          AI-generated content may be incorrect
        </Text>
      </div>
    </div>
  );
}
