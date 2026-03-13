/**
 * Chat history slice — conversation list CRUD via async thunks.
 * createAsyncThunk replaces inline fetch + manual state updates in ChatHistory.tsx.
 * Granular selectors for each piece of history state.
 */
import { createSlice, createAsyncThunk, type PayloadAction } from '@reduxjs/toolkit';
import { httpClient } from '../api';

export interface ConversationSummary {
  id: string;
  title: string;
  lastMessage: string;
  timestamp: string;
  messageCount: number;
}

interface ChatHistoryState {
  conversations: ConversationSummary[];
  isLoading: boolean;
  error: string | null;
  showAll: boolean;
  isClearAllDialogOpen: boolean;
  isClearing: boolean;
}

const initialState: ChatHistoryState = {
  conversations: [],
  isLoading: true,
  error: null,
  showAll: false,
  isClearAllDialogOpen: false,
  isClearing: false,
};

/* ------------------------------------------------------------------ */
/*  Async Thunks                                                      */
/* ------------------------------------------------------------------ */

export const fetchConversations = createAsyncThunk(
  'chatHistory/fetchConversations',
  async () => {
    const data = await httpClient.get<{ conversations?: ConversationSummary[] }>('/conversations');
    return (data.conversations || []) as ConversationSummary[];
  },
);

export const deleteConversation = createAsyncThunk(
  'chatHistory/deleteConversation',
  async (conversationId: string) => {
    await httpClient.delete(`/conversations/${conversationId}`);
    return conversationId;
  },
);

export const renameConversation = createAsyncThunk(
  'chatHistory/renameConversation',
  async ({ conversationId, newTitle }: { conversationId: string; newTitle: string }) => {
    await httpClient.put(`/conversations/${conversationId}`, { title: newTitle });
    return { conversationId, newTitle };
  },
);

export const clearAllConversations = createAsyncThunk(
  'chatHistory/clearAllConversations',
  async () => {
    await httpClient.delete('/conversations');
  },
);

/* ------------------------------------------------------------------ */
/*  Slice                                                             */
/* ------------------------------------------------------------------ */

const chatHistorySlice = createSlice({
  name: 'chatHistory',
  initialState,
  reducers: {
    setShowAll(state, action: PayloadAction<boolean>) {
      state.showAll = action.payload;
    },
    setIsClearAllDialogOpen(state, action: PayloadAction<boolean>) {
      state.isClearAllDialogOpen = action.payload;
    },
  },
  extraReducers: (builder) => {
    builder
      // Fetch
      .addCase(fetchConversations.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(fetchConversations.fulfilled, (state, action) => {
        state.conversations = action.payload;
        state.isLoading = false;
      })
      .addCase(fetchConversations.rejected, (state) => {
        state.error = 'Unable to load conversation history';
        state.conversations = [];
        state.isLoading = false;
      })
      // Delete single
      .addCase(deleteConversation.fulfilled, (state, action) => {
        state.conversations = state.conversations.filter((c) => c.id !== action.payload);
      })
      // Rename
      .addCase(renameConversation.fulfilled, (state, action) => {
        const conv = state.conversations.find((c) => c.id === action.payload.conversationId);
        if (conv) conv.title = action.payload.newTitle;
      })
      // Clear all
      .addCase(clearAllConversations.pending, (state) => {
        state.isClearing = true;
      })
      .addCase(clearAllConversations.fulfilled, (state) => {
        state.conversations = [];
        state.isClearing = false;
        state.isClearAllDialogOpen = false;
      })
      .addCase(clearAllConversations.rejected, (state) => {
        state.isClearing = false;
      });
  },
});

export const { setShowAll, setIsClearAllDialogOpen } =
  chatHistorySlice.actions;
export default chatHistorySlice.reducer;
