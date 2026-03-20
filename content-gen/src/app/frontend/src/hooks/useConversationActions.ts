import { useCallback } from 'react';

import type { ChatMessage, Product, CreativeBrief } from '../types';
import { createMessage, buildGeneratedContent } from '../utils';
import { httpClient } from '../api';
import {
  useAppDispatch,
  useAppSelector,
  selectUserId,
  selectConversationId,
  selectPendingBrief,
  selectSelectedProducts,
  resetChat,
  resetContent,
  setConversationId,
  setConversationTitle,
  setMessages,
  addMessage,
  setPendingBrief,
  setConfirmedBrief,
  setAwaitingClarification,
  setSelectedProducts,
  setAvailableProducts,
  setGeneratedContent,
  toggleChatHistory,
} from '../store';

/* ------------------------------------------------------------------ */
/*  Hook                                                               */
/* ------------------------------------------------------------------ */

/**
 * Encapsulates every conversation-level user action:
 *
 *  - Loading a saved conversation from history
 *  - Starting a brand-new conversation
 *  - Confirming / cancelling a creative brief
 *  - Starting over with products
 *  - Toggling a product selection
 *  - Toggling the chat-history sidebar
 *
 * All Redux reads/writes are internal so the consumer stays declarative.
 */
export function useConversationActions() {
  const dispatch = useAppDispatch();
  const userId = useAppSelector(selectUserId);
  const conversationId = useAppSelector(selectConversationId);
  const pendingBrief = useAppSelector(selectPendingBrief);
  const selectedProducts = useAppSelector(selectSelectedProducts);

  /* ------------------------------------------------------------ */
  /*  Select (load) a conversation from history                    */
  /* ------------------------------------------------------------ */
  const selectConversation = useCallback(
    async (selectedConversationId: string) => {
      try {
        const data = await httpClient.get<{
          messages?: {
            role: string;
            content: string;
            timestamp?: string;
            agent?: string;
          }[];
          brief?: unknown;
          generated_content?: Record<string, unknown>;
        }>(`/conversations/${selectedConversationId}`, {
          params: { user_id: userId },
        });

        dispatch(setConversationId(selectedConversationId));
        dispatch(setConversationTitle(null)); // Will use title from conversation list

        const loadedMessages: ChatMessage[] = (data.messages || []).map(
          (m, index) => ({
            id: `${selectedConversationId}-${index}`,
            role: m.role as 'user' | 'assistant',
            content: m.content,
            timestamp: m.timestamp || new Date().toISOString(),
            agent: m.agent,
          }),
        );
        dispatch(setMessages(loadedMessages));
        dispatch(setPendingBrief(null));
        dispatch(setAwaitingClarification(false));
        dispatch(
          setConfirmedBrief(
            (data.brief as CreativeBrief) || null,
          ),
        );

        // Restore availableProducts so product/color name detection works
        // when regenerating images in a restored conversation
        if (data.brief) {
          try {
            const productsData = await httpClient.get<{
              products?: Product[];
            }>('/products');
            dispatch(setAvailableProducts(productsData.products || []));
          } catch {
            // Non-critical — product load failure for restored conversation
          }
        }

        if (data.generated_content) {
          // eslint-disable-next-line @typescript-eslint/no-explicit-any
          const gc = data.generated_content as any;
          const restoredContent = buildGeneratedContent(gc, true);
          dispatch(setGeneratedContent(restoredContent));

          if (
            gc.selected_products &&
            Array.isArray(gc.selected_products)
          ) {
            dispatch(setSelectedProducts(gc.selected_products));
          } else {
            dispatch(setSelectedProducts([]));
          }
        } else {
          dispatch(setGeneratedContent(null));
          dispatch(setSelectedProducts([]));
        }
      } catch {
        // Error loading conversation — swallowed silently
      }
    },
    [userId, dispatch],
  );

  /* ------------------------------------------------------------ */
  /*  Start a new conversation                                     */
  /* ------------------------------------------------------------ */
  const newConversation = useCallback(() => {
    dispatch(resetChat(undefined));
    dispatch(resetContent());
  }, [dispatch]);

  /* ------------------------------------------------------------ */
  /*  Brief lifecycle                                              */
  /* ------------------------------------------------------------ */
  const confirmBrief = useCallback(async () => {
    if (!pendingBrief) return;

    try {
      const { confirmBrief: confirmBriefApi } = await import('../api');
      await confirmBriefApi(pendingBrief, conversationId, userId);
      dispatch(setConfirmedBrief(pendingBrief));
      dispatch(setPendingBrief(null));
      dispatch(setAwaitingClarification(false));

      const productsData = await httpClient.get<{ products?: Product[] }>(
        '/products',
      );
      dispatch(setAvailableProducts(productsData.products || []));

      dispatch(
        addMessage(
          createMessage(
            'assistant',
            "Great! Your creative brief has been confirmed. Here are the available products for your campaign. Select the ones you'd like to feature, or tell me what you're looking for.",
            'ProductAgent',
          ),
        ),
      );
    } catch {
      // Error confirming brief — swallowed silently
    }
  }, [conversationId, userId, pendingBrief, dispatch]);

  const cancelBrief = useCallback(() => {
    dispatch(setPendingBrief(null));
    dispatch(setAwaitingClarification(false));
    dispatch(
      addMessage(
        createMessage(
          'assistant',
          'No problem. Please provide your creative brief again or ask me any questions.',
        ),
      ),
    );
  }, [dispatch]);

  /* ------------------------------------------------------------ */
  /*  Product actions                                              */
  /* ------------------------------------------------------------ */
  const selectProduct = useCallback(
    (product: Product) => {
      const isSelected = selectedProducts.some(
        (p) =>
          (p.sku || p.product_name) ===
          (product.sku || product.product_name),
      );
      if (isSelected) {
        dispatch(setSelectedProducts([]));
      } else {
        // Single selection mode — replace any existing selection
        dispatch(setSelectedProducts([product]));
      }
    },
    [selectedProducts, dispatch],
  );

  /* ------------------------------------------------------------ */
  /*  Sidebar toggle                                               */
  /* ------------------------------------------------------------ */
  const toggleHistory = useCallback(() => {
    dispatch(toggleChatHistory());
  }, [dispatch]);

  return {
    selectConversation,
    newConversation,
    confirmBrief,
    cancelBrief,
    selectProduct,
    toggleHistory,
  };
}
