import {
  Text,
  Badge,
  tokens,
} from '@fluentui/react-components';
import {
  Checkmark20Regular,
} from '@fluentui/react-icons';
import type { CreativeBrief } from '../types';

interface ConfirmedBriefViewProps {
  brief: CreativeBrief;
}

const briefFields: { key: keyof CreativeBrief; label: string }[] = [
  { key: 'overview', label: 'Overview' },
  { key: 'objectives', label: 'Objectives' },
  { key: 'target_audience', label: 'Target Audience' },
  { key: 'key_message', label: 'Key Message' },
  { key: 'tone_and_style', label: 'Tone & Style' },
  { key: 'deliverable', label: 'Deliverable' },
  { key: 'timelines', label: 'Timelines' },
  { key: 'visual_guidelines', label: 'Visual Guidelines' },
  { key: 'cta', label: 'Call to Action' },
];

export function ConfirmedBriefView({ brief }: ConfirmedBriefViewProps) {
  return (
    <div className="message assistant" style={{ 
      width: '100%',
      alignSelf: 'flex-start',
      opacity: 0.85,
      backgroundColor: tokens.colorNeutralBackground3,
      padding: '12px 16px',
      borderRadius: '8px',
      margin: '16px 0 0 0',
    }}>
      {/* Header with confirmed badge */}
      <div style={{ 
        display: 'flex', 
        alignItems: 'center', 
        gap: '8px', 
        marginBottom: '12px' 
      }}>
        <Badge 
          appearance="filled" 
          size="small" 
          color="success"
          icon={<Checkmark20Regular />}
        >
          Brief Confirmed
        </Badge>
      </div>
      
      {/* Brief Fields - Compact bullet list */}
      <div style={{ 
        display: 'flex', 
        flexDirection: 'column', 
        gap: '6px',
        paddingLeft: '8px',
        borderLeft: `2px solid ${tokens.colorBrandBackground}`,
      }}>
        {briefFields.map(({ key, label }) => {
          const value = brief[key];
          if (!value?.trim()) return null;
          
          return (
            <div key={key}>
              <Text 
                weight="semibold" 
                size={200}
                style={{ color: tokens.colorNeutralForeground1 }}
              >
                {label}:
              </Text>
              {' '}
              <Text 
                size={200}
                style={{ 
                  color: tokens.colorNeutralForeground3,
                }}
              >
                {value}
              </Text>
            </div>
          );
        })}
      </div>
    </div>
  );
}
