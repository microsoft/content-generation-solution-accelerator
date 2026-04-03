/**
 * Chat slice — conversation state, messages, clarification flow.
 * Typed createSlice replaces scattered useState-based state in App.tsx.
 * Granular selectors for each piece of chat state.
 */
import { createSlice, type PayloadAction } from '@reduxjs/toolkit';
import { v4 as uuidv4 } from 'uuid';
import type { ChatMessage } from '../types';

interface ChatState {
  conversationId: string;
  conversationTitle: string | null;
  messages: ChatMessage[];
  awaitingClarification: boolean;
  historyRefreshTrigger: number;
}

const initialState: ChatState = {
  conversationId: uuidv4(),
  conversationTitle: null,
  messages: [],
  awaitingClarification: false,
  historyRefreshTrigger: 0,
};

const chatSlice = createSlice({
  name: 'chat',
  initialState,
  reducers: {
    setConversationId(state, action: PayloadAction<string>) {
      state.conversationId = action.payload;
    },
    setConversationTitle(state, action: PayloadAction<string | null>) {
      state.conversationTitle = action.payload;
    },
    setMessages(state, action: PayloadAction<ChatMessage[]>) {
      state.messages = action.payload;
    },
    addMessage(state, action: PayloadAction<ChatMessage>) {
      state.messages.push(action.payload);
    },
    setAwaitingClarification(state, action: PayloadAction<boolean>) {
      state.awaitingClarification = action.payload;
    },
    incrementHistoryRefresh(state) {
      state.historyRefreshTrigger += 1;
    },
    /** Reset chat to a fresh conversation. Optionally provide a new ID. */
    resetChat(state, action: PayloadAction<string | undefined>) {
      state.conversationId = action.payload ?? uuidv4();
      state.conversationTitle = null;
      state.messages = [];
      state.awaitingClarification = false;
    },
  },
});

export const {
  setConversationId,
  setConversationTitle,
  setMessages,
  addMessage,
  setAwaitingClarification,
  incrementHistoryRefresh,
  resetChat,
} = chatSlice.actions;
export default chatSlice.reducer;
