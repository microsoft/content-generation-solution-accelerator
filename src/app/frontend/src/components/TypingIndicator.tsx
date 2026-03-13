import { memo, useMemo } from 'react';
import {
  Button,
  Text,
  Tooltip,
  tokens,
} from '@fluentui/react-components';
import { Stop24Regular } from '@fluentui/react-icons';

export interface TypingIndicatorProps {
  /** Status text shown next to the dots (e.g. "Generating image…"). Falls back to "Thinking…". */
  statusText?: string;
  /** Callback wired to the Stop button. If omitted the button is hidden. */
  onStop?: () => void;
}

/**
 * Animated "thinking" indicator with optional status text and a Stop button.
 */
export const TypingIndicator = memo(function TypingIndicator({ statusText, onStop }: TypingIndicatorProps) {
  const dotStyle = useMemo(() => (delay: string): React.CSSProperties => ({
    width: '8px',
    height: '8px',
    borderRadius: '50%',
    backgroundColor: tokens.colorBrandBackground,
    animation: 'pulse 1.4s infinite ease-in-out',
    animationDelay: delay,
  }), []);

  return (
    <div
      className="typing-indicator"
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: '12px',
        padding: '12px 16px',
        backgroundColor: tokens.colorNeutralBackground3,
        borderRadius: '8px',
        alignSelf: 'flex-start',
        width: '100%',
      }}
    >
      <div className="thinking-dots">
        <span style={{ display: 'inline-flex', gap: '4px', alignItems: 'center' }}>
          <span className="dot" style={dotStyle('0s')} />
          <span className="dot" style={dotStyle('0.2s')} />
          <span className="dot" style={dotStyle('0.4s')} />
        </span>
      </div>

      <Text size={300} style={{ color: tokens.colorNeutralForeground2 }}>
        {statusText || 'Thinking...'}
      </Text>

      {onStop && (
        <Tooltip content="Stop generation" relationship="label">
          <Button
            appearance="subtle"
            icon={<Stop24Regular />}
            onClick={onStop}
            size="small"
            style={{
              color: tokens.colorPaletteRedForeground1,
              minWidth: '32px',
              marginLeft: 'auto',
            }}
          >
            Stop
          </Button>
        </Tooltip>
      )}
    </div>
  );
});
TypingIndicator.displayName = 'TypingIndicator';
