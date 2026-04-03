import { memo, useState, useCallback } from 'react';
import {
  Button,
  Text,
  Tooltip,
  tokens,
} from '@fluentui/react-components';
import { AI_DISCLAIMER } from '../utils';
import {
  Send20Regular,
  Add20Regular,
} from '@fluentui/react-icons';

export interface ChatInputProps {
  /** Called with the trimmed message text when the user submits. */
  onSendMessage: (message: string) => void;
  /** Called when the user clicks the "New chat" button. */
  onNewConversation?: () => void;
  /** Disables the input and buttons while a request is in flight. */
  disabled?: boolean;
  /** Allows the parent to drive the input value (e.g. from WelcomeCard suggestions). */
  value?: string;
  /** Notifies the parent when the user types. */
  onChange?: (value: string) => void;
}

/**
 * Chat input bar with send & new-chat buttons, plus an AI disclaimer.
 */
export const ChatInput = memo(function ChatInput({
  onSendMessage,
  onNewConversation,
  disabled = false,
  value: controlledValue,
  onChange: controlledOnChange,
}: ChatInputProps) {
  const [internalValue, setInternalValue] = useState('');

  // Support both controlled & uncontrolled modes
  const inputValue = controlledValue ?? internalValue;
  const setInputValue = useCallback((v: string) => {
    controlledOnChange?.(v);
    if (controlledValue === undefined) setInternalValue(v);
  }, [controlledOnChange, controlledValue]);

  const handleSubmit = useCallback((e: React.FormEvent) => {
    e.preventDefault();
    if (inputValue.trim() && !disabled) {
      onSendMessage(inputValue.trim());
      setInputValue('');
    }
  }, [inputValue, disabled, onSendMessage, setInputValue]);

  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  }, [handleSubmit]);

  return (
    <div style={{ margin: '0 8px 8px 8px', position: 'relative' }}>
      {/* Input Box */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          padding: '8px 12px',
          borderRadius: '4px',
          backgroundColor: tokens.colorNeutralBackground1,
          border: `1px solid ${tokens.colorNeutralStroke2}`,
        }}
      >
        <input
          type="text"
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Type a message"
          disabled={disabled}
          style={{
            flex: 1,
            border: 'none',
            outline: 'none',
            backgroundColor: 'transparent',
            fontFamily: 'var(--fontFamilyBase)',
            fontSize: '14px',
            color: tokens.colorNeutralForeground1,
          }}
        />

        {/* Icons on the right */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0px' }}>
          <Tooltip content="New chat" relationship="label">
            <Button
              appearance="subtle"
              icon={<Add20Regular />}
              size="small"
              onClick={onNewConversation}
              disabled={disabled}
              style={{
                minWidth: '32px',
                height: '32px',
                color: tokens.colorNeutralForeground3,
              }}
            />
          </Tooltip>

          {/* Vertical divider */}
          <div
            style={{
              width: '1px',
              height: '20px',
              backgroundColor: tokens.colorNeutralStroke2,
              margin: '0 4px',
            }}
          />

          <Button
            appearance="subtle"
            icon={<Send20Regular />}
            size="small"
            onClick={handleSubmit}
            disabled={!inputValue.trim() || disabled}
            style={{
              minWidth: '32px',
              height: '32px',
              color: inputValue.trim() ? tokens.colorBrandForeground1 : tokens.colorNeutralForeground4,
            }}
          />
        </div>
      </div>

      {/* Disclaimer */}
      <Text
        size={100}
        style={{
          display: 'block',
          marginTop: '8px',
          color: tokens.colorNeutralForeground4,
          fontSize: '12px',
        }}
      >
        {AI_DISCLAIMER}
      </Text>
    </div>
  );
});
ChatInput.displayName = 'ChatInput';
