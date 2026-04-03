import { memo, useState, useEffect, useRef, useCallback } from 'react';
import {
  Button,
  Text,
  tokens,
  Menu,
  MenuTrigger,
  MenuPopover,
  MenuList,
  MenuItem,
  Input,
  Dialog,
  DialogSurface,
  DialogTitle,
  DialogBody,
  DialogActions,
  DialogContent,
} from '@fluentui/react-components';
import {
  MoreHorizontal20Regular,
  Delete20Regular,
  Edit20Regular,
} from '@fluentui/react-icons';
import type { ConversationSummary } from '../store';

/* ------------------------------------------------------------------ */
/*  Validation constants & helper                                      */
/* ------------------------------------------------------------------ */

const NAME_MIN_LENGTH = 5;
const NAME_MAX_LENGTH = 50;

/** Returns an error message, or `''` when the value is valid. */
function validateConversationName(value: string): string {
  const trimmed = value.trim();
  if (trimmed === '') return 'Conversation name cannot be empty or contain only spaces';
  if (trimmed.length < NAME_MIN_LENGTH) return `Conversation name must be at least ${NAME_MIN_LENGTH} characters`;
  if (value.length > NAME_MAX_LENGTH) return `Conversation name cannot exceed ${NAME_MAX_LENGTH} characters`;
  if (!/[a-zA-Z0-9]/.test(trimmed)) return 'Conversation name must contain at least one letter or number';
  return '';
}

export interface ConversationItemProps {
  conversation: ConversationSummary;
  isActive: boolean;
  onSelect: () => void;
  onDelete: (conversationId: string) => void;
  onRename: (conversationId: string, newTitle: string) => void;
  onRefresh: () => void;
  disabled?: boolean;
}

/**
 * A single row in the chat-history sidebar —
 * title, context-menu (rename / delete) and confirmation dialogs.
 */
export const ConversationItem = memo(function ConversationItem({
  conversation,
  isActive,
  onSelect,
  onDelete,
  onRename,
  onRefresh,
  disabled = false,
}: ConversationItemProps) {
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [isRenameDialogOpen, setIsRenameDialogOpen] = useState(false);
  const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false);
  const [renameValue, setRenameValue] = useState(conversation.title || '');
  const [renameError, setRenameError] = useState<string>('');
  const renameInputRef = useRef<HTMLInputElement>(null);

  const handleRenameClick = useCallback(() => {
    setRenameValue(conversation.title || '');
    setRenameError('');
    setIsRenameDialogOpen(true);
    setIsMenuOpen(false);
  }, [conversation.title]);

  const handleRenameConfirm = useCallback(async () => {
    const error = validateConversationName(renameValue);
    if (error) {
      setRenameError(error);
      return;
    }

    const trimmedValue = renameValue.trim();
    if (trimmedValue === conversation.title) {
      setIsRenameDialogOpen(false);
      setRenameError('');
      return;
    }

    await onRename(conversation.id, trimmedValue);
    onRefresh();
    setIsRenameDialogOpen(false);
    setRenameError('');
  }, [renameValue, conversation.id, conversation.title, onRename, onRefresh]);

  const handleDeleteClick = useCallback(() => {
    setIsDeleteDialogOpen(true);
    setIsMenuOpen(false);
  }, []);

  const handleDeleteConfirm = useCallback(async () => {
    await onDelete(conversation.id);
    setIsDeleteDialogOpen(false);
  }, [conversation.id, onDelete]);

  useEffect(() => {
    if (isRenameDialogOpen && renameInputRef.current) {
      renameInputRef.current.focus();
      renameInputRef.current.select();
    }
  }, [isRenameDialogOpen]);

  return (
    <>
      <div
        onClick={disabled ? undefined : onSelect}
        style={{
          padding: '8px',
          cursor: disabled ? 'not-allowed' : 'pointer',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: '8px',
          backgroundColor: isActive ? tokens.colorNeutralBackground1 : 'transparent',
          border: isActive
            ? `1px solid ${tokens.colorNeutralStroke2}`
            : '1px solid transparent',
          borderRadius: '6px',
          marginLeft: '-8px',
          marginRight: '-8px',
          transition: 'background-color 0.15s, border-color 0.15s',
          opacity: disabled ? 0.5 : 1,
          pointerEvents: disabled ? 'none' : 'auto',
        }}
      >
        <Text
          size={200}
          weight={isActive ? 'semibold' : 'regular'}
          style={{
            overflow: 'hidden',
            textOverflow: 'ellipsis',
            whiteSpace: 'nowrap',
            flex: 1,
            fontSize: '13px',
            color: tokens.colorNeutralForeground1,
          }}
        >
          {conversation.title || 'Untitled'}
        </Text>

        <Menu open={isMenuOpen} onOpenChange={(_, data) => setIsMenuOpen(data.open)}>
          <MenuTrigger disableButtonEnhancement>
            <Button
              appearance="subtle"
              icon={<MoreHorizontal20Regular />}
              size="small"
              onClick={(e) => {
                e.stopPropagation();
              }}
              style={{
                minWidth: '24px',
                height: '24px',
                padding: '2px',
                color: tokens.colorNeutralForeground3,
              }}
            />
          </MenuTrigger>
          <MenuPopover>
            <MenuList>
              <MenuItem
                icon={<Edit20Regular />}
                onClick={(e) => {
                  e.stopPropagation();
                  handleRenameClick();
                }}
              >
                Rename
              </MenuItem>
              <MenuItem
                icon={<Delete20Regular />}
                onClick={(e) => {
                  e.stopPropagation();
                  handleDeleteClick();
                }}
              >
                Delete
              </MenuItem>
            </MenuList>
          </MenuPopover>
        </Menu>
      </div>

      {/* Rename dialog */}
      <Dialog open={isRenameDialogOpen} onOpenChange={(_, data) => setIsRenameDialogOpen(data.open)}>
        <DialogSurface>
          <DialogTitle>Rename conversation</DialogTitle>
          <DialogBody>
            <DialogContent>
              <Input
                ref={renameInputRef}
                value={renameValue}
                maxLength={NAME_MAX_LENGTH}
                onChange={(e) => {
                  const newValue = e.target.value;
                  setRenameValue(newValue);
                  setRenameError(validateConversationName(newValue));
                }}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && renameValue.trim()) {
                    handleRenameConfirm();
                  } else if (e.key === 'Escape') {
                    setIsRenameDialogOpen(false);
                  }
                }}
                placeholder="Enter conversation name"
                style={{ width: '100%' }}
              />
              <Text
                size={200}
                style={{
                  color: tokens.colorNeutralForeground3,
                  marginTop: '4px',
                  display: 'block',
                }}
              >
                Maximum {NAME_MAX_LENGTH} characters ({renameValue.length}/{NAME_MAX_LENGTH})
              </Text>
              {renameError && (
                <Text
                  size={200}
                  style={{
                    color: tokens.colorPaletteRedForeground1,
                    marginTop: '8px',
                    display: 'block',
                  }}
                >
                  {renameError}
                </Text>
              )}
            </DialogContent>
          </DialogBody>
          <DialogActions style={{ marginTop: '8px', paddingTop: '8px', paddingBottom: '8px' }}>
            <Button
              appearance="secondary"
              onClick={() => {
                setIsRenameDialogOpen(false);
                setRenameError('');
              }}
            >
              Cancel
            </Button>
            <Button
              appearance="primary"
              onClick={handleRenameConfirm}
              disabled={!!validateConversationName(renameValue)}
            >
              Rename
            </Button>
          </DialogActions>
        </DialogSurface>
      </Dialog>

      {/* Delete dialog */}
      <Dialog open={isDeleteDialogOpen} onOpenChange={(_, data) => setIsDeleteDialogOpen(data.open)}>
        <DialogSurface>
          <DialogTitle>Delete conversation</DialogTitle>
          <DialogBody>
            <DialogContent>
              <Text>
                Are you sure you want to delete &quot;{conversation.title || 'Untitled'}&quot;? This action
                cannot be undone.
              </Text>
            </DialogContent>
          </DialogBody>
          <DialogActions>
            <Button appearance="secondary" onClick={() => setIsDeleteDialogOpen(false)}>
              Cancel
            </Button>
            <Button appearance="primary" onClick={handleDeleteConfirm}>
              Delete
            </Button>
          </DialogActions>
        </DialogSurface>
      </Dialog>
    </>
  );
});
ConversationItem.displayName = 'ConversationItem';
