import { useState, useEffect, useCallback, useRef } from 'react';
import {
  Button,
  Text,
  Spinner,
  tokens,
  Link,
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
  Chat24Regular,
  MoreHorizontal20Regular,
  Compose20Regular,
  Delete20Regular,
  Edit20Regular,
} from '@fluentui/react-icons';

interface ConversationSummary {
  id: string;
  title: string;
  lastMessage: string;
  timestamp: string;
  messageCount: number;
}

interface ChatHistoryProps {
  currentConversationId: string;
  currentMessages?: { role: string; content: string }[]; // Current session messages
  onSelectConversation: (conversationId: string) => void;
  onNewConversation: () => void;
  refreshTrigger?: number; // Increment to trigger refresh
  isGenerating?: boolean; // True when content generation is in progress
}

export function ChatHistory({ 
  currentConversationId, 
  currentMessages = [],
  onSelectConversation,
  onNewConversation,
  refreshTrigger = 0,
  isGenerating = false
}: ChatHistoryProps) {
  const [conversations, setConversations] = useState<ConversationSummary[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showAll, setShowAll] = useState(false);
  const INITIAL_COUNT = 5;

  const handleDeleteConversation = useCallback(async (conversationId: string) => {
    try {
      const response = await fetch(`/api/conversations/${conversationId}`, {
        method: 'DELETE',
      });
      if (response.ok) {
        setConversations(prev => prev.filter(c => c.id !== conversationId));
        if (conversationId === currentConversationId) {
          onNewConversation();
        }
      } else {
        console.error('Failed to delete conversation');
      }
    } catch (err) {
      console.error('Error deleting conversation:', err);
    }
  }, [currentConversationId, onNewConversation]);

  const handleRenameConversation = useCallback(async (conversationId: string, newTitle: string) => {
    try {
      const response = await fetch(`/api/conversations/${conversationId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ title: newTitle }),
      });
      
      if (response.ok) {
        setConversations(prev => prev.map(c => 
          c.id === conversationId ? { ...c, title: newTitle } : c
        ));
      } else {
        console.error('Failed to rename conversation');
      }
    } catch (err) {
      console.error('Error renaming conversation:', err);
    }
  }, []);

  const loadConversations = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      // Backend gets user from auth headers, no need to pass user_id
      const response = await fetch('/api/conversations');
      if (response.ok) {
        const data = await response.json();
        setConversations(data.conversations || []);
      } else {
        // If no conversations endpoint, use empty list
        setConversations([]);
      }
    } catch (err) {
      console.error('Error loading conversations:', err);
      setError('Unable to load conversation history');
      setConversations([]);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    loadConversations();
  }, [loadConversations, refreshTrigger]);

  // Reset showAll when conversations change significantly
  useEffect(() => {
    setShowAll(false);
  }, [refreshTrigger]);

  // Build the current session conversation summary if it has messages
  const currentSessionConversation: ConversationSummary | null = currentMessages.length > 0 ? {
    id: currentConversationId,
    title: currentMessages.find(m => m.role === 'user')?.content?.substring(0, 50) || 'Current Conversation',
    lastMessage: currentMessages[currentMessages.length - 1]?.content?.substring(0, 100) || '',
    timestamp: new Date().toISOString(),
    messageCount: currentMessages.length,
  } : null;

  // Merge current session with saved conversations, updating the current one with live data
  const displayConversations = (() => {
    // Find if current conversation exists in saved list
    const existingIndex = conversations.findIndex(c => c.id === currentConversationId);
    
    if (existingIndex >= 0 && currentSessionConversation) {
      // Update the saved conversation with current session data (live message count)
      const updated = [...conversations];
      updated[existingIndex] = {
        ...updated[existingIndex],
        messageCount: currentMessages.length,
        lastMessage: currentMessages[currentMessages.length - 1]?.content?.substring(0, 100) || updated[existingIndex].lastMessage,
      };
      return updated;
    } else if (currentSessionConversation) {
      // Add current session at the top if it has messages and isn't saved yet
      return [currentSessionConversation, ...conversations];
    }
    return conversations;
  })();

  const visibleConversations = showAll ? displayConversations : displayConversations.slice(0, INITIAL_COUNT);
  const hasMore = displayConversations.length > INITIAL_COUNT;

  return (
    <div style={{ 
      height: '100%', 
      display: 'flex', 
      flexDirection: 'column',
      padding: '16px',
      backgroundColor: tokens.colorNeutralBackground3,
      overflow: 'hidden',
    }}>
      <Text 
        weight="semibold" 
        size={300}
        style={{ 
          marginBottom: '12px',
          color: tokens.colorNeutralForeground1,
          flexShrink: 0,
        }}
      >
        Chat History
      </Text>

      <div style={{ 
        borderBottom: `1px solid ${tokens.colorNeutralStroke2}`,
        marginBottom: '12px',
        flexShrink: 0,
      }} />

      <div style={{ 
        flex: 1, 
        display: 'flex',
        flexDirection: 'column',
        minHeight: 0,
        overflowY: showAll ? 'auto' : 'hidden',
        paddingLeft: '8px',
        paddingRight: '8px',
        marginLeft: '-8px',
        marginRight: '-8px',
      }}>
        {isLoading ? (
          <div style={{ 
            display: 'flex', 
            justifyContent: 'center', 
            alignItems: 'center',
            padding: '32px' 
          }}>
            <Spinner size="small" label="Loading..." />
          </div>
        ) : error ? (
          <div style={{ 
            textAlign: 'center', 
            padding: '32px',
            color: tokens.colorNeutralForeground3 
          }}>
            <Text size={200}>{error}</Text>
            <Link 
              onClick={loadConversations}
              style={{ display: 'block', marginTop: '8px' }}
            >
              Retry
            </Link>
          </div>
        ) : displayConversations.length === 0 ? (
          <div style={{ 
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            padding: '32px',
            color: tokens.colorNeutralForeground3 
          }}>
            <Chat24Regular style={{ fontSize: '24px', marginBottom: '8px', opacity: 0.5 }} />
            <Text size={200} block>No conversations yet</Text>
          </div>
        ) : (
          <>
            {visibleConversations.map((conversation) => (
              <ConversationItem
                key={conversation.id}
                conversation={conversation}
                isActive={conversation.id === currentConversationId}
                onSelect={() => onSelectConversation(conversation.id)}
                onDelete={handleDeleteConversation}
                onRename={handleRenameConversation}
                onRefresh={loadConversations}
                disabled={isGenerating}
              />
            ))}
          </>
        )}

        <div style={{ 
          marginTop: '8px',
          display: 'flex',
          flexDirection: 'column',
          gap: '12px',
          flexShrink: 0,
          ...(showAll && {
            position: 'sticky',
            bottom: 0,
            backgroundColor: tokens.colorNeutralBackground3,
            paddingTop: '8px',
            paddingBottom: '4px',
          }),
        }}>
          {hasMore && (
            <Link
              onClick={isGenerating ? undefined : () => setShowAll(!showAll)}
              style={{
                fontSize: '13px',
                color: isGenerating ? tokens.colorNeutralForegroundDisabled : tokens.colorBrandForeground1,
                cursor: isGenerating ? 'not-allowed' : 'pointer',
                pointerEvents: isGenerating ? 'none' : 'auto',
              }}
            >
              {showAll ? 'Show less' : 'See all'}
            </Link>
          )}
          <Link
            onClick={isGenerating ? undefined : onNewConversation}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              fontSize: '13px',
              color: isGenerating ? tokens.colorNeutralForegroundDisabled : tokens.colorNeutralForeground1,
              cursor: isGenerating ? 'not-allowed' : 'pointer',
              pointerEvents: isGenerating ? 'none' : 'auto',
            }}
          >
            <Compose20Regular />
            Start new chat
          </Link>
        </div>
      </div>
    </div>
  );
}

interface ConversationItemProps {
  conversation: ConversationSummary;
  isActive: boolean;
  onSelect: () => void;
  onDelete: (conversationId: string) => void;
  onRename: (conversationId: string, newTitle: string) => void;
  onRefresh: () => void;
  disabled?: boolean;
}

function ConversationItem({ 
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
  const renameInputRef = useRef<HTMLInputElement>(null);

  const handleRenameClick = () => {
    setRenameValue(conversation.title || '');
    setIsRenameDialogOpen(true);
    setIsMenuOpen(false);
  };

  const handleRenameConfirm = async () => {
    const trimmedValue = renameValue.trim();
    if (trimmedValue && trimmedValue !== conversation.title) {
      await onRename(conversation.id, trimmedValue);
      onRefresh();
    }
    setIsRenameDialogOpen(false);
  };

  const handleDeleteClick = () => {
    setIsDeleteDialogOpen(true);
    setIsMenuOpen(false);
  };

  const handleDeleteConfirm = async () => {
    await onDelete(conversation.id);
    setIsDeleteDialogOpen(false);
  };

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
          backgroundColor: isActive 
            ? tokens.colorNeutralBackground1 
            : 'transparent',
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

      <Dialog open={isRenameDialogOpen} onOpenChange={(_, data) => setIsRenameDialogOpen(data.open)}>
        <DialogSurface>
          <DialogTitle>Rename conversation</DialogTitle>
          <DialogBody>
            <DialogContent>
              <Input
                ref={renameInputRef}
                value={renameValue}
                onChange={(e) => setRenameValue(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    handleRenameConfirm();
                  } else if (e.key === 'Escape') {
                    setIsRenameDialogOpen(false);
                  }
                }}
                placeholder="Enter conversation name"
                style={{ width: '100%' }}
              />
            </DialogContent>
          </DialogBody>
          <DialogActions style={{ marginTop: '8px', paddingTop: '8px', paddingBottom: '8px' }}>
            <Button appearance="secondary" onClick={() => setIsRenameDialogOpen(false)}>
              Cancel
            </Button>
            <Button appearance="primary" onClick={handleRenameConfirm}>
              Rename
            </Button>
          </DialogActions>
        </DialogSurface>
      </Dialog>

      <Dialog open={isDeleteDialogOpen} onOpenChange={(_, data) => setIsDeleteDialogOpen(data.open)}>
        <DialogSurface>
          <DialogTitle>Delete conversation</DialogTitle>
          <DialogBody>
            <DialogContent>
              <Text>
                Are you sure you want to delete "{conversation.title || 'Untitled'}"? This action cannot be undone.
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
}
