import { useEffect, useRef } from 'react';

import { ChatPanel } from './components/ChatPanel';
import { ChatHistory } from './components/ChatHistory';
import { AppHeader } from './components/AppHeader';
import {
  useAppDispatch,
  useAppSelector,
  fetchAppConfig,
  fetchUserInfo,
  selectUserName,
  selectShowChatHistory,
} from './store';
import { useChatOrchestrator, useContentGeneration, useConversationActions } from './hooks';


function App() {
  const dispatch = useAppDispatch();
  const userName = useAppSelector(selectUserName);
  const showChatHistory = useAppSelector(selectShowChatHistory);

  // Shared abort controller for chat & content-generation
  const abortControllerRef = useRef<AbortController | null>(null);

  // Business-logic hooks
  const { sendMessage } = useChatOrchestrator(abortControllerRef);
  const { generateContent, stopGeneration } = useContentGeneration(abortControllerRef);
  const {
    selectConversation,
    newConversation,
    confirmBrief,
    cancelBrief,
    selectProduct,
    toggleHistory,
  } = useConversationActions();

  // Fetch app config & current user on mount
  useEffect(() => {
    dispatch(fetchAppConfig());
    dispatch(fetchUserInfo());
  }, [dispatch]);

  return (
    <div className="app-container">
      {/* Header */}
      <AppHeader
        userName={userName}
        showChatHistory={showChatHistory}
        onToggleChatHistory={toggleHistory}
      />

      {/* Main Content */}
      <div className="main-content">
        {/* Chat Panel - main area */}
        <div className="chat-panel">
          <ChatPanel
            onSendMessage={sendMessage}
            onStopGeneration={stopGeneration}
            onBriefConfirm={confirmBrief}
            onBriefCancel={cancelBrief}
            onGenerateContent={generateContent}
            onRegenerateContent={generateContent}
            onProductSelect={selectProduct}
            onNewConversation={newConversation}
          />
        </div>

        {/* Chat History Sidebar - RIGHT side */}
        {showChatHistory && (
          <div className="history-panel">
            <ChatHistory
              onSelectConversation={selectConversation}
              onNewConversation={newConversation}
            />
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
