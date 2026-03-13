/**
 * Redux store — central state for the application.
 * configureStore combines all domain-specific slices.
 */
import { configureStore } from '@reduxjs/toolkit';
import appReducer from './appSlice';
import chatReducer from './chatSlice';
import contentReducer from './contentSlice';
import chatHistoryReducer from './chatHistorySlice';

export const store = configureStore({
  reducer: {
    app: appReducer,
    chat: chatReducer,
    content: contentReducer,
    chatHistory: chatHistoryReducer,
  },
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;
