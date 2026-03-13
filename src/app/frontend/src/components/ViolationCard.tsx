import { memo, useMemo } from 'react';
import {
  Text,
} from '@fluentui/react-components';
import {
  ErrorCircle20Regular,
  Warning20Regular,
  Info20Regular,
} from '@fluentui/react-icons';
import type { ComplianceViolation } from '../types';

export interface ViolationCardProps {
  violation: ComplianceViolation;
}

/**
 * A single compliance violation row with severity-coloured icon and background.
 */
export const ViolationCard = memo(function ViolationCard({ violation }: ViolationCardProps) {
  const { icon, bg } = useMemo(() => {
    switch (violation.severity) {
      case 'error':
        return {
          icon: <ErrorCircle20Regular style={{ color: '#d13438' }} />,
          bg: '#fde7e9',
        };
      case 'warning':
        return {
          icon: <Warning20Regular style={{ color: '#ffb900' }} />,
          bg: '#fff4ce',
        };
      case 'info':
        return {
          icon: <Info20Regular style={{ color: '#0078d4' }} />,
          bg: '#deecf9',
        };
    }
  }, [violation.severity]);

  return (
    <div
      style={{
        padding: '8px 12px',
        backgroundColor: bg,
        borderRadius: '4px',
        marginBottom: '4px',
        display: 'flex',
        alignItems: 'flex-start',
        gap: '8px',
      }}
    >
      {icon}
      <div>
        <Text weight="semibold" size={200} block>
          {violation.message}
        </Text>
        <Text size={100} style={{ color: '#616161' }}>
          {violation.suggestion}
        </Text>
      </div>
    </div>
  );
});
ViolationCard.displayName = 'ViolationCard';
