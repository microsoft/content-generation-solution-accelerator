import { memo, useCallback } from 'react';
import {
  Text,
  Badge,
  Button,
  Tooltip,
  tokens,
} from '@fluentui/react-components';
import { Copy20Regular } from '@fluentui/react-icons';
import ReactMarkdown from 'react-markdown';
import type { ChatMessage } from '../types';
import { useCopyToClipboard } from '../hooks';
import { AI_DISCLAIMER } from '../utils';

export interface MessageBubbleProps {
  message: ChatMessage;
}

/**
 * Renders a single chat message — user or assistant.
 *
 * - User messages: right-aligned, brand-coloured bubble.
 * - Assistant messages: left-aligned, full-width, with optional agent badge,
 *   markdown rendering, copy button and AI disclaimer.
 */
export const MessageBubble = memo(function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === 'user';
  const { copied, copy } = useCopyToClipboard();
  const handleCopy = useCallback(() => copy(message.content), [copy, message.content]);

  return (
    <div
      className={`message ${isUser ? 'user' : 'assistant'}`}
      style={{
        display: 'inline-block',
        wordWrap: 'break-word',
        wordBreak: 'break-word',
        boxSizing: 'border-box',
        ...(isUser
          ? {
              backgroundColor: tokens.colorBrandBackground2,
              color: tokens.colorNeutralForeground1,
              alignSelf: 'flex-end',
              padding: '12px 16px',
              borderRadius: '8px',
              maxWidth: '80%',
            }
          : {
              backgroundColor: tokens.colorNeutralBackground3,
              color: tokens.colorNeutralForeground1,
              alignSelf: 'flex-start',
              margin: '16px 0 0 0',
              padding: '12px 16px',
              borderRadius: '8px',
              width: '100%',
            }),
      }}
    >
      {/* Agent badge for assistant messages */}
      {!isUser && message.agent && (
        <Badge appearance="outline" size="small" style={{ marginBottom: '8px' }}>
          {message.agent}
        </Badge>
      )}

      {/* Message content with markdown */}
      <div
        className="message-content"
        style={{
          display: 'flex',
          flexDirection: 'column',
          whiteSpace: 'pre-wrap',
          width: '100%',
        }}
      >
        <ReactMarkdown>{message.content}</ReactMarkdown>

        {/* Footer for assistant messages */}
        {!isUser && (
          <div
            className="assistant-footer"
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              marginTop: '12px',
            }}
          >
            <Text
              size={100}
              style={{
                color: tokens.colorNeutralForeground4,
                fontSize: '11px',
              }}
            >
              {AI_DISCLAIMER}
            </Text>

            <div className="assistant-actions" style={{ display: 'flex', gap: '4px' }}>
              <Tooltip content={copied ? 'Copied!' : 'Copy'} relationship="label">
                <Button
                  appearance="subtle"
                  icon={<Copy20Regular />}
                  size="small"
                  onClick={handleCopy}
                  style={{
                    minWidth: '28px',
                    height: '28px',
                    color: tokens.colorNeutralForeground3,
                  }}
                />
              </Tooltip>
            </div>
          </div>
        )}
      </div>
    </div>
  );
});
MessageBubble.displayName = 'MessageBubble';
