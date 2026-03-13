import { memo } from 'react';
import {
  Card,
  Text,
  tokens,
} from '@fluentui/react-components';

export interface SuggestionCardProps {
  title: string;
  icon: string;
  isSelected?: boolean;
  onClick: () => void;
}

/**
 * A single suggestion prompt card shown on the WelcomeCard screen.
 * Handles its own hover / selected styling.
 */
export const SuggestionCard = memo(function SuggestionCard({
  title,
  icon,
  isSelected = false,
  onClick,
}: SuggestionCardProps) {
  return (
    <Card
      onClick={onClick}
      style={{
        padding: 'clamp(12px, 2vw, 16px)',
        cursor: 'pointer',
        backgroundColor: isSelected
          ? tokens.colorBrandBackground2
          : tokens.colorNeutralBackground1,
        border: 'none',
        borderRadius: '16px',
        transition: 'all 0.2s ease',
      }}
      onMouseEnter={(e) => {
        if (!isSelected) {
          e.currentTarget.style.backgroundColor = tokens.colorBrandBackground2;
        }
      }}
      onMouseLeave={(e) => {
        if (!isSelected) {
          e.currentTarget.style.backgroundColor = tokens.colorNeutralBackground1;
        }
      }}
    >
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: 'clamp(8px, 1.5vw, 12px)',
        }}
      >
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            width: 'clamp(32px, 5vw, 40px)',
            height: 'clamp(32px, 5vw, 40px)',
            minWidth: '32px',
            minHeight: '32px',
            flexShrink: 0,
          }}
        >
          <img
            src={icon}
            alt="Prompt icon"
            style={{ width: '100%', height: '100%', objectFit: 'contain' }}
          />
        </div>
        <div style={{ minWidth: 0, flex: 1 }}>
          <Text size={300} block style={{ fontSize: 'clamp(13px, 1.8vw, 15px)' }}>
            {title}
          </Text>
        </div>
      </div>
    </Card>
  );
});
SuggestionCard.displayName = 'SuggestionCard';
