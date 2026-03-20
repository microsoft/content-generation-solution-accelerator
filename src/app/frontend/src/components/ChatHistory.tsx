import { useEffect, useCallback, useMemo, memo } from 'react';
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
  DismissCircle20Regular,
} from '@fluentui/react-icons';
import {
  useAppDispatch,
  useAppSelector,
  fetchConversations,
  deleteConversation,
  renameConversation,
  clearAllConversations,
  setShowAll as setShowAllAction,
  setIsClearAllDialogOpen,
  selectConversations,
  selectIsHistoryLoading,
  selectHistoryError,
  selectShowAll,
  selectIsClearAllDialogOpen,
  selectIsClearing,
  selectConversationId,
  selectConversationTitle,
  selectMessages,
  selectIsLoading,
  selectHistoryRefreshTrigger,
} from '../store';
import type { ConversationSummary } from '../store';
import { ConversationItem } from './ConversationItem';

interface ChatHistoryProps {
  onSelectConversation: (conversationId: string) => void;
  onNewConversation: () => void;
}

export const ChatHistory = memo(function ChatHistory({ 
  onSelectConversation,
  onNewConversation,
}: ChatHistoryProps) {
  const dispatch = useAppDispatch();
  const conversations = useAppSelector(selectConversations);
  const isLoading = useAppSelector(selectIsHistoryLoading);
  const error = useAppSelector(selectHistoryError);
  const showAll = useAppSelector(selectShowAll);
  const isClearAllDialogOpen = useAppSelector(selectIsClearAllDialogOpen);
  const isClearing = useAppSelector(selectIsClearing);
  const currentConversationId = useAppSelector(selectConversationId);
  const currentConversationTitle = useAppSelector(selectConversationTitle);
  const currentMessages = useAppSelector(selectMessages);
  const isGenerating = useAppSelector(selectIsLoading);
  const refreshTrigger = useAppSelector(selectHistoryRefreshTrigger);

  const INITIAL_COUNT = 5;

  const handleClearAllConversations = useCallback(async () => {
    try {
      await dispatch(clearAllConversations()).unwrap();
      onNewConversation();
    } catch {
      // Error clearing all conversations
    }
  }, [dispatch, onNewConversation]);

  const handleDeleteConversation = useCallback(async (conversationId: string) => {
    try {
      await dispatch(deleteConversation(conversationId)).unwrap();
      if (conversationId === currentConversationId) {
        onNewConversation();
      }
    } catch {
      // Error deleting conversation
    }
  }, [dispatch, currentConversationId, onNewConversation]);

  const handleRenameConversation = useCallback(async (conversationId: string, newTitle: string) => {
    try {
      await dispatch(renameConversation({ conversationId, newTitle })).unwrap();
    } catch {
      // Error renaming conversation
    }
  }, [dispatch]);

  useEffect(() => {
    dispatch(fetchConversations());
  }, [dispatch, refreshTrigger]);

  // Reset showAll when conversations change significantly
  useEffect(() => {
    dispatch(setShowAllAction(false));
  }, [dispatch, refreshTrigger]);

  // Build the current session conversation summary if it has messages
  const currentSessionConversation = useMemo<ConversationSummary | null>(() => 
    currentMessages.length > 0 && currentConversationTitle ? {
      id: currentConversationId,
      title: currentConversationTitle,
      lastMessage: currentMessages[currentMessages.length - 1]?.content?.substring(0, 100) || '',
      timestamp: new Date().toISOString(),
      messageCount: currentMessages.length,
    } : null,
    [currentMessages, currentConversationId, currentConversationTitle],
  );

  // Merge current session with saved conversations, updating the current one with live data
  const displayConversations = useMemo(() => {
    const existingIndex = conversations.findIndex(c => c.id === currentConversationId);
    
    if (existingIndex >= 0 && currentSessionConversation) {
      const updated = [...conversations];
      updated[existingIndex] = {
        ...updated[existingIndex],
        messageCount: currentMessages.length,
        lastMessage: currentMessages[currentMessages.length - 1]?.content?.substring(0, 100) || updated[existingIndex].lastMessage,
      };
      return updated;
    } else if (currentSessionConversation) {
      return [currentSessionConversation, ...conversations];
    }
    return conversations;
  }, [conversations, currentConversationId, currentSessionConversation, currentMessages]);

  const visibleConversations = useMemo(
    () => showAll ? displayConversations : displayConversations.slice(0, INITIAL_COUNT),
    [showAll, displayConversations],
  );
  const hasMore = displayConversations.length > INITIAL_COUNT;

  const handleRefreshConversations = useCallback(() => {
    dispatch(fetchConversations());
  }, [dispatch]);

  return (
    <div style={{ 
      height: '100%', 
      display: 'flex', 
      flexDirection: 'column',
      padding: '16px',
      backgroundColor: tokens.colorNeutralBackground3,
      overflow: 'hidden',
    }}>
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: '12px',
        flexShrink: 0,
      }}>
        <Text 
          weight="semibold" 
          size={300}
          style={{ 
            color: tokens.colorNeutralForeground1,
          }}
        >
          Chat History
        </Text>
        <Menu>
          <MenuTrigger disableButtonEnhancement>
            <Button
              appearance="subtle"
              icon={<MoreHorizontal20Regular />}
              size="small"
              title="More options"
              disabled={isGenerating}
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
                icon={<DismissCircle20Regular />}
                onClick={() => dispatch(setIsClearAllDialogOpen(true))}
                disabled={displayConversations.length === 0}
              >
                Clear all chat history
              </MenuItem>
            </MenuList>
          </MenuPopover>
        </Menu>
      </div>

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
              onClick={handleRefreshConversations}
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
                onRefresh={handleRefreshConversations}
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
              onClick={isGenerating ? undefined : () => dispatch(setShowAllAction(!showAll))}
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

      {/* Clear All Confirmation Dialog */}
      <Dialog open={isClearAllDialogOpen} onOpenChange={(_, data) => !isClearing && dispatch(setIsClearAllDialogOpen(data.open))}>
        <DialogSurface>
          <DialogTitle>Clear all chat history</DialogTitle>
          <DialogBody>
            <DialogContent>
              <Text>
                Are you sure you want to delete all chat history? This action cannot be undone and all conversations will be permanently removed.
              </Text>
            </DialogContent>
          </DialogBody>
          <DialogActions>
            <Button appearance="secondary" onClick={() => dispatch(setIsClearAllDialogOpen(false))} disabled={isClearing}>
              Cancel
            </Button>
            <Button appearance="primary" onClick={handleClearAllConversations} disabled={isClearing}>
              {isClearing ? 'Clearing...' : 'Clear All'}
            </Button>
          </DialogActions>
        </DialogSurface>
      </Dialog>
    </div>
  );
});

ChatHistory.displayName = 'ChatHistory';
