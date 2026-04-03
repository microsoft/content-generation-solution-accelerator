import { memo } from 'react';
import {
  Text,
  Avatar,
  Button,
  Tooltip,
  tokens,
} from '@fluentui/react-components';
import {
  History24Regular,
  History24Filled,
} from '@fluentui/react-icons';
import ContosoLogo from '../styles/images/contoso.svg';

export interface AppHeaderProps {
  userName?: string | null;
  showChatHistory: boolean;
  onToggleChatHistory: () => void;
}

/**
 * Top-level application header with logo, title, history toggle and avatar.
 */
export const AppHeader = memo(function AppHeader({ userName, showChatHistory, onToggleChatHistory }: AppHeaderProps) {
  return (
    <header
      style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: 'clamp(8px, 1.5vw, 12px) clamp(16px, 3vw, 24px)',
        borderBottom: `1px solid ${tokens.colorNeutralStroke2}`,
        backgroundColor: tokens.colorNeutralBackground1,
        flexShrink: 0,
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: 'clamp(8px, 1.5vw, 10px)' }}>
        <img src={ContosoLogo} alt="Contoso" width="28" height="28" />
        <Text
          weight="semibold"
          size={500}
          style={{
            color: tokens.colorNeutralForeground1,
            fontSize: 'clamp(16px, 2.5vw, 20px)',
          }}
        >
          Contoso
        </Text>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
        <Tooltip
          content={showChatHistory ? 'Hide chat history' : 'Show chat history'}
          relationship="label"
        >
          <Button
            appearance="subtle"
            icon={showChatHistory ? <History24Filled /> : <History24Regular />}
            onClick={onToggleChatHistory}
            aria-label={showChatHistory ? 'Hide chat history' : 'Show chat history'}
          />
        </Tooltip>
        <Avatar name={userName || undefined} color="colorful" size={36} />
      </div>
    </header>
  );
});
AppHeader.displayName = 'AppHeader';
