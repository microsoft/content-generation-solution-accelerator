import { useCallback, type MutableRefObject } from 'react';

import type { AgentResponse, GeneratedContent } from '../types';
import { createMessage, createErrorMessage, matchesAnyKeyword, createNameSwapper } from '../utils';
import {
  useAppDispatch,
  useAppSelector,
  selectConversationId,
  selectUserId,
  selectPendingBrief,
  selectConfirmedBrief,
  selectAwaitingClarification,
  selectSelectedProducts,
  selectAvailableProducts,
  selectGeneratedContent,
  addMessage,
  setIsLoading,
  setGenerationStatus,
  GenerationStatus,
  setPendingBrief,
  setConfirmedBrief,
  setAwaitingClarification,
  setSelectedProducts,
  setGeneratedContent,
  incrementHistoryRefresh,
  selectConversationTitle,
  setConversationTitle,
} from '../store';
import type { AppDispatch } from '../store';

/* ------------------------------------------------------------------ */
/*  Shared helper — consumes a streamChat generator and dispatches     */
/*  the final assistant message.  Used by branches 1-b, 3-b, 4-b.     */
/* ------------------------------------------------------------------ */

async function consumeStreamChat(
  stream: AsyncGenerator<AgentResponse>,
  dispatch: AppDispatch,
): Promise<void> {
  let fullContent = '';
  let currentAgent = '';
  let messageAdded = false;

  for await (const response of stream) {
    if (response.type === 'agent_response') {
      fullContent = response.content;
      currentAgent = response.agent || '';
      if ((response.is_final || response.requires_user_input) && !messageAdded) {
        dispatch(addMessage(createMessage('assistant', fullContent, currentAgent)));
        messageAdded = true;
      }
    } else if (response.type === 'error') {
      dispatch(
        addMessage(
          createMessage(
            'assistant',
            response.content || 'An error occurred while processing your request.',
          ),
        ),
      );
      messageAdded = true;
    }
  }
}

/* ------------------------------------------------------------------ */
/*  Hook                                                               */
/* ------------------------------------------------------------------ */

/**
 * Orchestrates the entire "send a message" flow.
 *
 * Depending on the current conversation phase it will:
 *  - refine a pending brief (PlanningAgent)
 *  - answer a general question while a brief is pending (streamChat)
 *  - forward a product-selection request (ProductAgent)
 *  - regenerate an image (ImageAgent)
 *  - parse a new creative brief (PlanningAgent)
 *  - fall through to generic chat (streamChat)
 *
 * All Redux reads/writes happen inside the hook so the caller is kept
 * thin and declarative.
 *
 * @param abortControllerRef Shared ref that lets the parent (or sibling
 *        hooks) cancel the in-flight request.
 * @returns `{ sendMessage }` — the callback to wire into `ChatPanel`.
 */
export function useChatOrchestrator(
  abortControllerRef: MutableRefObject<AbortController | null>,
) {
  const dispatch = useAppDispatch();
  const conversationId = useAppSelector(selectConversationId);
  const userId = useAppSelector(selectUserId);
  const pendingBrief = useAppSelector(selectPendingBrief);
  const confirmedBrief = useAppSelector(selectConfirmedBrief);
  const awaitingClarification = useAppSelector(selectAwaitingClarification);
  const selectedProducts = useAppSelector(selectSelectedProducts);
  const availableProducts = useAppSelector(selectAvailableProducts);
  const generatedContent = useAppSelector(selectGeneratedContent);
  const conversationTitle = useAppSelector(selectConversationTitle);

  const sendMessage = useCallback(
    async (content: string) => {
      dispatch(addMessage(createMessage('user', content)));
      dispatch(setIsLoading(true));

      // Create new abort controller for this request
      abortControllerRef.current = new AbortController();
      const signal = abortControllerRef.current.signal;

      try {
        // Dynamic imports to keep the initial bundle lean
        const { streamChat, parseBrief, selectProducts } = await import(
          '../api'
        );

        /* ---------------------------------------------------------- */
        /*  Branch 1 – pending brief, not yet confirmed               */
        /* ---------------------------------------------------------- */
        if (pendingBrief && !confirmedBrief) {
          const refinementKeywords = [
            'change', 'update', 'modify', 'add', 'remove', 'delete',
            'set', 'make', 'should be',
          ] as const;
          const isRefinement = matchesAnyKeyword(content, refinementKeywords);

          if (isRefinement || awaitingClarification) {
            // --- 1-a  Refine the brief --------------------------------
            const refinementPrompt = `Current creative brief:\n${JSON.stringify(pendingBrief, null, 2)}\n\nUser requested change: ${content}\n\nPlease update the brief accordingly and return the complete updated brief.`;

            dispatch(setGenerationStatus(GenerationStatus.UPDATING_BRIEF));
            const parsed = await parseBrief(
              refinementPrompt,
              conversationId,
              userId,
              signal,
            );

            if (parsed.generated_title && !conversationTitle) {
              dispatch(setConversationTitle(parsed.generated_title));
            }

            if (parsed.brief) {
              dispatch(setPendingBrief(parsed.brief));
            }

            if (parsed.requires_clarification && parsed.clarifying_questions) {
              dispatch(setAwaitingClarification(true));
              dispatch(setGenerationStatus(GenerationStatus.IDLE));
              dispatch(
                addMessage(
                  createMessage('assistant', parsed.clarifying_questions, 'PlanningAgent'),
                ),
              );
            } else {
              dispatch(setAwaitingClarification(false));
              dispatch(setGenerationStatus(GenerationStatus.IDLE));
              dispatch(
                addMessage(
                  createMessage(
                    'assistant',
                    "I've updated the brief based on your feedback. Please review the changes above. Let me know if you'd like any other modifications, or click **Confirm Brief** when you're satisfied.",
                    'PlanningAgent',
                  ),
                ),
              );
            }
          } else {
            // --- 1-b  General question while brief is pending -----------
            dispatch(setGenerationStatus(GenerationStatus.PROCESSING_QUESTION));
            await consumeStreamChat(
              streamChat(content, conversationId, userId, signal),
              dispatch,
            );
            dispatch(setGenerationStatus(GenerationStatus.IDLE));
          }

          /* ---------------------------------------------------------- */
          /*  Branch 2 – brief confirmed, in product selection          */
          /* ---------------------------------------------------------- */
        } else if (confirmedBrief && !generatedContent) {
          dispatch(setGenerationStatus(GenerationStatus.FINDING_PRODUCTS));
          const result = await selectProducts(
            content,
            selectedProducts,
            conversationId,
            userId,
            signal,
          );
          dispatch(setSelectedProducts(result.products || []));
          dispatch(setGenerationStatus(GenerationStatus.IDLE));
          dispatch(
            addMessage(
              createMessage(
                'assistant',
                result.message || 'Products updated.',
                'ProductAgent',
              ),
            ),
          );

          /* ---------------------------------------------------------- */
          /*  Branch 3 – content generated, post-generation phase       */
          /* ---------------------------------------------------------- */
        } else if (generatedContent && confirmedBrief) {
          const imageModificationKeywords = [
            'change', 'modify', 'update', 'replace', 'show', 'display',
            'use', 'instead', 'different', 'another', 'make it', 'make the',
            'kitchen', 'dining', 'living', 'bedroom', 'bathroom', 'outdoor',
            'office', 'room', 'scene', 'setting', 'background', 'style',
            'color', 'lighting',
          ] as const;
          const isImageModification = matchesAnyKeyword(content, imageModificationKeywords);

          if (isImageModification) {
            // --- 3-a  Regenerate image --------------------------------
            const { streamRegenerateImage } = await import('../api');
            dispatch(
              setGenerationStatus(GenerationStatus.REGENERATING_IMAGE),
            );

            let responseData: GeneratedContent | null = null;
            let messageContent = '';

            // Detect if user mentions a different product
            const mentionedProduct = availableProducts.find((p) =>
              content.toLowerCase().includes(p.product_name.toLowerCase()),
            );
            const productsForRequest = mentionedProduct
              ? [mentionedProduct]
              : selectedProducts;

            const previousPrompt =
              generatedContent.image_content?.prompt_used;

            for await (const response of streamRegenerateImage(
              content,
              confirmedBrief,
              productsForRequest,
              previousPrompt,
              conversationId,
              userId,
              signal,
            )) {
              if (response.type === 'heartbeat') {
                dispatch(
                  setGenerationStatus({
                    status: GenerationStatus.POLLING,
                    label: response.message || 'Regenerating image...',
                  }),
                );
              } else if (
                response.type === 'agent_response' &&
                response.is_final
              ) {
                try {
                  const parsedContent = JSON.parse(response.content);

                  if (
                    parsedContent.image_url ||
                    parsedContent.image_base64
                  ) {
                    // Replace old product name in text_content when switching
                    const swapName = createNameSwapper(
                      selectedProducts[0]?.product_name,
                      mentionedProduct?.product_name,
                    );
                    const tc = generatedContent.text_content;

                    responseData = {
                      ...generatedContent,
                      text_content: mentionedProduct
                        ? {
                            ...tc,
                            headline: swapName?.(tc?.headline) ?? tc?.headline,
                            body: swapName?.(tc?.body) ?? tc?.body,
                            tagline: swapName?.(tc?.tagline) ?? tc?.tagline,
                            cta_text: swapName?.(tc?.cta_text) ?? tc?.cta_text,
                          }
                        : tc,
                      image_content: {
                        ...generatedContent.image_content,
                        image_url:
                          parsedContent.image_url ||
                          generatedContent.image_content?.image_url,
                        image_base64: parsedContent.image_base64,
                        prompt_used:
                          parsedContent.image_prompt ||
                          generatedContent.image_content?.prompt_used,
                      },
                    };
                    dispatch(setGeneratedContent(responseData));

                    if (mentionedProduct) {
                      dispatch(setSelectedProducts([mentionedProduct]));
                    }

                    // Update confirmed brief to include the modification
                    const updatedBrief = {
                      ...confirmedBrief,
                      visual_guidelines: `${confirmedBrief.visual_guidelines}. User modification: ${content}`,
                    };
                    dispatch(setConfirmedBrief(updatedBrief));

                    messageContent =
                      parsedContent.message ||
                      'Image regenerated with your requested changes.';
                  } else if (parsedContent.error) {
                    messageContent = parsedContent.error;
                  } else {
                    messageContent =
                      parsedContent.message || 'I processed your request.';
                  }
                } catch {
                  messageContent =
                    response.content || 'Image regenerated.';
                }
              } else if (response.type === 'error') {
                messageContent =
                  response.content ||
                  'An error occurred while regenerating the image.';
              }
            }

            dispatch(setGenerationStatus(GenerationStatus.IDLE));
            dispatch(
              addMessage(createMessage('assistant', messageContent, 'ImageAgent')),
            );
          } else {
            // --- 3-b  General question after content generation --------
            dispatch(setGenerationStatus(GenerationStatus.PROCESSING_REQUEST));
            await consumeStreamChat(
              streamChat(content, conversationId, userId, signal),
              dispatch,
            );
            dispatch(setGenerationStatus(GenerationStatus.IDLE));
          }

          /* ---------------------------------------------------------- */
          /*  Branch 4 – default: initial flow                          */
          /* ---------------------------------------------------------- */
        } else {
          const briefKeywords = [
            'campaign', 'marketing', 'target audience', 'objective',
            'deliverable',
          ] as const;
          const isBriefLike = matchesAnyKeyword(content, briefKeywords);

          if (isBriefLike && !confirmedBrief) {
            // --- 4-a  Parse as creative brief --------------------------
            dispatch(setGenerationStatus(GenerationStatus.ANALYZING_BRIEF));
            const parsed = await parseBrief(
              content,
              conversationId,
              userId,
              signal,
            );

            if (parsed.generated_title && !conversationTitle) {
              dispatch(setConversationTitle(parsed.generated_title));
            }

            if (parsed.rai_blocked) {
              dispatch(setGenerationStatus(GenerationStatus.IDLE));
              dispatch(
                addMessage(
                  createMessage('assistant', parsed.message, 'ContentSafety'),
                ),
              );
            } else if (
              parsed.requires_clarification &&
              parsed.clarifying_questions
            ) {
              if (parsed.brief) {
                dispatch(setPendingBrief(parsed.brief));
              }
              dispatch(setAwaitingClarification(true));
              dispatch(setGenerationStatus(GenerationStatus.IDLE));
              dispatch(
                addMessage(
                  createMessage(
                    'assistant',
                    parsed.clarifying_questions,
                    'PlanningAgent',
                  ),
                ),
              );
            } else {
              if (parsed.brief) {
                dispatch(setPendingBrief(parsed.brief));
              }
              dispatch(setAwaitingClarification(false));
              dispatch(setGenerationStatus(GenerationStatus.IDLE));
              dispatch(
                addMessage(
                  createMessage(
                    'assistant',
                    "I've parsed your creative brief. Please review the details below and let me know if you'd like to make any changes. You can say things like \"change the target audience to...\" or \"add a call to action...\". When everything looks good, click **Confirm Brief** to proceed.",
                    'PlanningAgent',
                  ),
                ),
              );
            }
          } else {
            // --- 4-b  Generic chat -----------------------------------
            dispatch(setGenerationStatus(GenerationStatus.PROCESSING_REQUEST));
            await consumeStreamChat(
              streamChat(content, conversationId, userId, signal),
              dispatch,
            );
            dispatch(setGenerationStatus(GenerationStatus.IDLE));
          }
        }
      } catch (error) {
        if (error instanceof Error && error.name === 'AbortError') {
          dispatch(addMessage(createMessage('assistant', 'Generation stopped.')));
        } else {
          dispatch(
            addMessage(
              createErrorMessage(
                'Sorry, there was an error processing your request. Please try again.',
              ),
            ),
          );
        }
      } finally {
        dispatch(setIsLoading(false));
        dispatch(setGenerationStatus(GenerationStatus.IDLE));
        abortControllerRef.current = null;
        dispatch(incrementHistoryRefresh());
      }
    },
    [
      conversationId,
      userId,
      confirmedBrief,
      pendingBrief,
      selectedProducts,
      generatedContent,
      availableProducts,
      dispatch,
      awaitingClarification,
      conversationTitle,
      abortControllerRef,
    ],
  );

  return { sendMessage };
}
