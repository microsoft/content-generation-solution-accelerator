/**
 * All Redux selectors in one place.
 * Importing RootState here (and ONLY here) avoids the circular dependency
 * between store.ts ↔ slice files that confuses VS Code's TypeScript server.
 */
import type { RootState } from './store';

/* ---- App selectors ---- */
export const selectUserId = (state: RootState) => state.app.userId;
export const selectUserName = (state: RootState) => state.app.userName;
export const selectIsLoading = (state: RootState) => state.app.isLoading;
export const selectGenerationStatusLabel = (state: RootState) => state.app.generationStatusLabel;
export const selectImageGenerationEnabled = (state: RootState) => state.app.imageGenerationEnabled;
export const selectShowChatHistory = (state: RootState) => state.app.showChatHistory;

/* ---- Chat selectors ---- */
export const selectConversationId = (state: RootState) => state.chat.conversationId;
export const selectConversationTitle = (state: RootState) => state.chat.conversationTitle;
export const selectMessages = (state: RootState) => state.chat.messages;
export const selectAwaitingClarification = (state: RootState) => state.chat.awaitingClarification;
export const selectHistoryRefreshTrigger = (state: RootState) => state.chat.historyRefreshTrigger;

/* ---- Content selectors ---- */
export const selectPendingBrief = (state: RootState) => state.content.pendingBrief;
export const selectConfirmedBrief = (state: RootState) => state.content.confirmedBrief;
export const selectSelectedProducts = (state: RootState) => state.content.selectedProducts;
export const selectAvailableProducts = (state: RootState) => state.content.availableProducts;
export const selectGeneratedContent = (state: RootState) => state.content.generatedContent;

/* ---- Chat History selectors ---- */
export const selectConversations = (state: RootState) => state.chatHistory.conversations;
export const selectIsHistoryLoading = (state: RootState) => state.chatHistory.isLoading;
export const selectHistoryError = (state: RootState) => state.chatHistory.error;
export const selectShowAll = (state: RootState) => state.chatHistory.showAll;
export const selectIsClearAllDialogOpen = (state: RootState) => state.chatHistory.isClearAllDialogOpen;
export const selectIsClearing = (state: RootState) => state.chatHistory.isClearing;
