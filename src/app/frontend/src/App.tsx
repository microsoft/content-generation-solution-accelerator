import { useState, useCallback, useEffect, useRef } from 'react';
import {
  Text,
  Avatar,
  Button,
  Tooltip,
  tokens,
} from '@fluentui/react-components';
import {
  History24Regular,
  History24Filled,
} from '@fluentui/react-icons';
import { v4 as uuidv4 } from 'uuid';

import { ChatPanel } from './components/ChatPanel';
import { ChatHistory } from './components/ChatHistory';
import type { ChatMessage, CreativeBrief, Product, GeneratedContent } from './types';
import ContosoLogo from './styles/images/contoso.svg';


function App() {
  const [conversationId, setConversationId] = useState<string>(() => uuidv4());
  const [conversationTitle, setConversationTitle] = useState<string | null>(null);
  const [userId, setUserId] = useState<string>('');
  const [userName, setUserName] = useState<string>('');
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [generationStatus, setGenerationStatus] = useState<string>('');
  
  // Feature flags from config
  const [imageGenerationEnabled, setImageGenerationEnabled] = useState<boolean>(true);
  
  // Brief confirmation flow
  const [pendingBrief, setPendingBrief] = useState<CreativeBrief | null>(null);
  const [confirmedBrief, setConfirmedBrief] = useState<CreativeBrief | null>(null);
  
  // Product selection
  const [selectedProducts, setSelectedProducts] = useState<Product[]>([]);
  const [availableProducts, setAvailableProducts] = useState<Product[]>([]);
  
  // Generated content
  const [generatedContent, setGeneratedContent] = useState<GeneratedContent | null>(null);

  // Trigger for refreshing chat history
  const [historyRefreshTrigger, setHistoryRefreshTrigger] = useState(0);

  // Toggle for showing/hiding chat history panel
  const [showChatHistory, setShowChatHistory] = useState(true);

  // Abort controller for cancelling ongoing requests
  const abortControllerRef = useRef<AbortController | null>(null);

  // Fetch app config on mount
  useEffect(() => {
    const fetchConfig = async () => {
      try {
        const { getAppConfig } = await import('./api');
        const config = await getAppConfig();
        setImageGenerationEnabled(config.enable_image_generation);
      } catch (err) {
        console.error('Error fetching config:', err);
        // Default to enabled if config fetch fails
        setImageGenerationEnabled(true);
      }
    };
    fetchConfig();
  }, []);

  // Fetch current user on mount - using /.auth/me (Azure App Service built-in auth endpoint)
  useEffect(() => {
    const fetchUser = async () => {
      try {
        const response = await fetch('/.auth/me');
        if (response.ok) {
          const payload = await response.json();
          
          // Extract user ID from objectidentifier claim
          const userClaims = payload[0]?.user_claims || [];
          const objectIdClaim = userClaims.find(
            (claim: { typ: string; val: string }) =>
              claim.typ === 'http://schemas.microsoft.com/identity/claims/objectidentifier'
          );
          setUserId(objectIdClaim?.val || 'anonymous');
          
          // Extract display name from 'name' claim
          const nameClaim = userClaims.find(
            (claim: { typ: string; val: string }) => claim.typ === 'name'
          );
          setUserName(nameClaim?.val || '');
        }
      } catch (err) {
        console.error('Error fetching user:', err);
        setUserId('anonymous');
        setUserName('');
      }
    };
    fetchUser();
  }, []);

  // Handle selecting a conversation from history
  const handleSelectConversation = useCallback(async (selectedConversationId: string) => {
    try {
      const response = await fetch(`/api/conversations/${selectedConversationId}?user_id=${encodeURIComponent(userId)}`);
      if (response.ok) {
        const data = await response.json();
        setConversationId(selectedConversationId);
        setConversationTitle(null); // Will use title from conversation list
        const loadedMessages: ChatMessage[] = (data.messages || []).map((msg: { role: string; content: string; timestamp?: string; agent?: string }, index: number) => ({
          id: `${selectedConversationId}-${index}`,
          role: msg.role as 'user' | 'assistant',
          content: msg.content,
          timestamp: msg.timestamp || new Date().toISOString(),
          agent: msg.agent,
        }));
        setMessages(loadedMessages);
        
        // Only set confirmedBrief if the brief was actually confirmed
        // Check metadata.brief_confirmed flag or if content was generated (implying confirmation)
        const briefWasConfirmed = data.metadata?.brief_confirmed || data.generated_content;
        if (briefWasConfirmed && data.brief) {
          setConfirmedBrief(data.brief);
          setPendingBrief(null);
        } else if (data.brief) {
          // Brief exists but wasn't confirmed - show it as pending for confirmation
          setPendingBrief(data.brief);
          setConfirmedBrief(null);
        } else {
          setPendingBrief(null);
          setConfirmedBrief(null);
        }
        
        // Restore availableProducts so product/color name detection works
        // when regenerating images in a restored conversation
        if (data.brief && availableProducts.length === 0) {
          try {
            const productsResponse = await fetch('/api/products');
            if (productsResponse.ok) {
              const productsData = await productsResponse.json();
              setAvailableProducts(productsData.products || []);
            }
          } catch (err) {
            console.error('Error loading products for restored conversation:', err);
          }
        }
        
        if (data.generated_content) {
          const gc = data.generated_content;
          let textContent = gc.text_content;
          if (typeof textContent === 'string') {
            try {
              textContent = JSON.parse(textContent);
            } catch {
            }
          }
          
          let imageUrl: string | undefined = gc.image_url;
          if (imageUrl && imageUrl.includes('blob.core.windows.net')) {
            const parts = imageUrl.split('/');
            const filename = parts[parts.length - 1];
            const convId = parts[parts.length - 2];
            imageUrl = `/api/images/${convId}/${filename}`;
          }
          if (!imageUrl && gc.image_base64) {
            imageUrl = `data:image/png;base64,${gc.image_base64}`;
          }
          
          const restoredContent: GeneratedContent = {
            text_content: typeof textContent === 'object' && textContent ? {
              headline: textContent?.headline,
              body: textContent?.body,
              cta_text: textContent?.cta,
              tagline: textContent?.tagline,
            } : undefined,
            image_content: (imageUrl || gc.image_prompt) ? {
              image_url: imageUrl,
              prompt_used: gc.image_prompt,
              alt_text: gc.image_revised_prompt || 'Generated marketing image',
            } : undefined,
            violations: gc.violations || [],
            requires_modification: gc.requires_modification || false,
            error: gc.error,
            image_error: gc.image_error,
            text_error: gc.text_error,
          };
          setGeneratedContent(restoredContent);
          
          if (gc.selected_products && Array.isArray(gc.selected_products)) {
            setSelectedProducts(gc.selected_products);
          } else {
            setSelectedProducts([]);
          }
        } else {
          setGeneratedContent(null);
          setSelectedProducts([]);
        }
      }
    } catch (error) {
      console.error('Error loading conversation:', error);
    }
  }, [userId, availableProducts.length]);

  // Handle starting a new conversation
  const handleNewConversation = useCallback(() => {
    setConversationId(uuidv4());
    setConversationTitle(null);
    setMessages([]);
    setPendingBrief(null);
    setConfirmedBrief(null);
    setGeneratedContent(null);
    setSelectedProducts([]);
  }, []);

  const handleSendMessage = useCallback(async (content: string) => {
    const userMessage: ChatMessage = {
      id: uuidv4(),
      role: 'user',
      content,
      timestamp: new Date().toISOString(),
    };
    
    setMessages(prev => [...prev, userMessage]);
    setIsLoading(true);
    setGenerationStatus('Processing your request...');
    
    // Create new abort controller for this request
    abortControllerRef.current = new AbortController();
    const signal = abortControllerRef.current.signal;
    
    try {
      const { sendMessage } = await import('./api');
      
      let productsToSend = selectedProducts;
      if (generatedContent && confirmedBrief && availableProducts.length > 0) {
        const contentLower = content.toLowerCase();
        const mentionedProduct = availableProducts.find(p =>
          contentLower.includes(p.product_name.toLowerCase())
        );
        if (mentionedProduct && mentionedProduct.product_name !== selectedProducts[0]?.product_name) {
          productsToSend = [mentionedProduct];
        }
      }
      
      // Send message - include brief if confirmed, products if we have them
      const response = await sendMessage({
        conversation_id: conversationId,
        user_id: userId,
        message: content,
        ...(confirmedBrief && { brief: confirmedBrief }),
        ...(productsToSend.length > 0 && { selected_products: productsToSend }),
        ...(generatedContent && { has_generated_content: true }),
      }, signal);
            
      // Handle response based on action_type
      switch (response.action_type) {
        case 'brief_parsed': {
          const brief = response.data?.brief as CreativeBrief | undefined;
          const title = response.data?.generated_title as string | undefined;
          if (brief) {
            setPendingBrief(brief);
          }
          if (title && !conversationTitle) {
            setConversationTitle(title);
          }
          break;
        }
        
        case 'clarification_needed': {
          const brief = response.data?.brief as CreativeBrief | undefined;
          if (brief) {
            setPendingBrief(brief);
          }
          break;
        }
        
        case 'brief_confirmed': {
          const brief = response.data?.brief as CreativeBrief | undefined;
          const products = response.data?.products as Product[] | undefined;
          if (brief) {
            setConfirmedBrief(brief);
            setPendingBrief(null);
          }
          if (products) {
            setAvailableProducts(products);
          }
          break;
        }
        
        case 'products_selected': {
          const products = response.data?.products as Product[] | undefined;
          if (products) {
            setSelectedProducts(products);
          }
          break;
        }
        
        case 'content_generated': {
          const generatedContent = response.data?.generated_content as GeneratedContent | undefined;
          if (generatedContent) {
            setGeneratedContent(generatedContent);
          }
          break;
        }
        
        case 'image_regenerated': {
          const generatedContent = response.data?.generated_content as GeneratedContent | undefined;
          if (generatedContent) {
            setGeneratedContent(generatedContent);
          }
          break;
        }
        
        case 'regeneration_started': {
          // Poll for completion using task_id from response
          // Backend already started the regeneration task via /api/chat
          const { pollTaskStatus } = await import('./api');
          const taskId = response.data?.task_id as string;
          
          if (!taskId) {
            throw new Error('No task_id received for regeneration');
          }
          
          setGenerationStatus('Regenerating image...');
          
          for await (const event of pollTaskStatus(taskId, signal)) {
            
            if (event.type === 'heartbeat') {
              const statusMessage = (event.content as string) || 'Regenerating image...';
              const elapsed = (event as { elapsed?: number }).elapsed || 0;
              setGenerationStatus(elapsed > 0 ? `${statusMessage} (${elapsed}s)` : statusMessage);
            } else if (event.type === 'agent_response' && event.is_final) {
              let result: Record<string, unknown> | undefined = event.content as unknown as Record<string, unknown>;
              if (typeof event.content === 'string') {
                try { result = JSON.parse(event.content); } catch { result = {}; }
              }
              
              let imageUrl = result?.image_url as string | undefined;
              if (imageUrl && imageUrl.includes('blob.core.windows.net')) {
                const parts = imageUrl.split('/');
                const filename = parts[parts.length - 1];
                const convId = parts[parts.length - 2];
                imageUrl = `/api/images/${convId}/${filename}`;
              }
              
              // Parse text_content if it's a JSON string
              let textContent = result?.text_content;
              if (typeof textContent === 'string') {
                try { textContent = JSON.parse(textContent); } catch { /* keep as-is */ }
              }
              
              // Update selected products if backend provided new ones (product change)
              const newProducts = result?.selected_products as Product[] | undefined;
              if (newProducts && newProducts.length > 0) {
                setSelectedProducts(newProducts);
              }
              
              // Update confirmed brief if backend provided an updated one (with accumulated modifications)
              const updatedBrief = result?.updated_brief as CreativeBrief | undefined;
              if (updatedBrief) {
                setConfirmedBrief(updatedBrief);
              }
              
              setGeneratedContent(prev => ({
                ...prev,
                // Update text content if provided (with new product name)
                text_content: textContent ? {
                  headline: (textContent as Record<string, unknown>).headline as string | undefined,
                  body: (textContent as Record<string, unknown>).body as string | undefined,
                  cta_text: (textContent as Record<string, unknown>).cta as string | undefined,
                } : prev?.text_content,
                image_content: imageUrl ? {
                  image_url: imageUrl,
                  prompt_used: result?.image_prompt as string | undefined,
                  alt_text: (result?.image_revised_prompt as string) || 'Regenerated marketing image',
                } : prev?.image_content,
                violations: prev?.violations || [],
                requires_modification: prev?.requires_modification || false,
              }));
            } else if (event.type === 'error') {
              throw new Error(event.content || 'Regeneration failed');
            }
          }
          
          setGenerationStatus('');
          break;
        }
        
        case 'start_over': {
          setPendingBrief(null);
          setConfirmedBrief(null);
          setSelectedProducts([]);
          setGeneratedContent(null);
          break;
        }
        
        case 'rai_blocked':
        case 'error':
        case 'chat_response':
        default:
          // Just show the message
          break;
      }
      
      // Add assistant message from response
      if (response.message) {
        const assistantMessage: ChatMessage = {
          id: uuidv4(),
          role: 'assistant',
          content: response.message,
          timestamp: new Date().toISOString(),
        };
        setMessages(prev => [...prev, assistantMessage]);
      }
      
    } catch (error) {
      // Check if this was a user-initiated cancellation
      if (error instanceof Error && error.name === 'AbortError') {
        console.log('Request cancelled by user');
        const cancelMessage: ChatMessage = {
          id: uuidv4(),
          role: 'assistant',
          content: 'Generation stopped.',
          timestamp: new Date().toISOString(),
        };
        setMessages(prev => [...prev, cancelMessage]);
      } else {
        console.error('Error sending message:', error);
        const errorMessage: ChatMessage = {
          id: uuidv4(),
          role: 'assistant',
          content: 'Sorry, there was an error processing your request. Please try again.',
          timestamp: new Date().toISOString(),
        };
        setMessages(prev => [...prev, errorMessage]);
      }
    } finally {
      setIsLoading(false);
      setGenerationStatus('');
      abortControllerRef.current = null;
      // Trigger refresh of chat history after message is sent
      setHistoryRefreshTrigger(prev => prev + 1);
    }
  }, [conversationId, userId, conversationTitle, confirmedBrief, selectedProducts, generatedContent]);

  const handleBriefConfirm = useCallback(async () => {
    if (!pendingBrief) return;
    
    try {
      const { sendMessage } = await import('./api');
      
      const response = await sendMessage({
        conversation_id: conversationId,
        user_id: userId,
        action: 'confirm_brief',
        brief: pendingBrief,
      });
            
      // Update state based on response 
      if (response.action_type === 'brief_confirmed') {
        const brief = response.data?.brief as CreativeBrief | undefined;
        if (brief) {
          setConfirmedBrief(brief);
        } else {
          setConfirmedBrief(pendingBrief);
        }
        setPendingBrief(null);
        
        // Fetch products separately after confirmation
        try {
          const productsResponse = await fetch('/api/products');
          if (productsResponse.ok) {
            const productsData = await productsResponse.json();
            setAvailableProducts(productsData.products || []);
          }
        } catch (err) {
          console.error('Error loading products after confirmation:', err);
        }
      }
      
      // Add assistant message
      if (response.message) {
        const assistantMessage: ChatMessage = {
          id: uuidv4(),
          role: 'assistant',
          content: response.message,
          agent: 'ProductAgent',
          timestamp: new Date().toISOString(),
        };
        setMessages(prev => [...prev, assistantMessage]);
      }
    } catch (error) {
      console.error('Error confirming brief:', error);
    }
  }, [conversationId, userId, pendingBrief]);

  const handleBriefCancel = useCallback(async () => {
    setPendingBrief(null);
    
    const assistantMessage: ChatMessage = {
      id: uuidv4(),
      role: 'assistant',
      content: 'No problem. Please provide your creative brief again or ask me any questions.',
      timestamp: new Date().toISOString(),
    };
    setMessages(prev => [...prev, assistantMessage]);
  }, []);

  const handleProductsStartOver = useCallback(async () => {
    try {
      const { sendMessage } = await import('./api');
      
      const response = await sendMessage({
        conversation_id: conversationId,
        user_id: userId,
        action: 'start_over',
      });
      
      console.log('Start over response:', response);
      
      // Reset all local state
      setPendingBrief(null);
      setConfirmedBrief(null);
      setSelectedProducts([]);
      setGeneratedContent(null);
      
      // Add assistant message
      if (response.message) {
        const assistantMessage: ChatMessage = {
          id: uuidv4(),
          role: 'assistant',
          content: response.message,
          timestamp: new Date().toISOString(),
        };
        setMessages(prev => [...prev, assistantMessage]);
      }
    } catch (error) {
      console.error('Error starting over:', error);
      // Still reset local state even if backend call fails
      setPendingBrief(null);
      setConfirmedBrief(null);
      setSelectedProducts([]);
      setGeneratedContent(null);
      
      const assistantMessage: ChatMessage = {
        id: uuidv4(),
        role: 'assistant',
        content: 'Starting over. Please provide your creative brief to begin a new campaign.',
        timestamp: new Date().toISOString(),
      };
      setMessages(prev => [...prev, assistantMessage]);
    }
  }, [conversationId, userId]);

  const handleProductSelect = useCallback((product: Product) => {
    const isSelected = selectedProducts.some(
      p => (p.sku || p.product_name) === (product.sku || product.product_name)
    );
    
    if (isSelected) {
      // Deselect - but user must have at least one selected to proceed
      setSelectedProducts([]);
    } else {
      // Single selection mode - replace any existing selection
      setSelectedProducts([product]);
    }
  }, [selectedProducts]);

  const handleStopGeneration = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
  }, []);

  const handleGenerateContent = useCallback(async () => {
    if (!confirmedBrief) return;
    
    setIsLoading(true);
    setGenerationStatus('Starting content generation...');
    
    // Create new abort controller for this request
    abortControllerRef.current = new AbortController();
    const signal = abortControllerRef.current.signal;
    
    try {
      const { streamGenerateContent } = await import('./api');
      
      for await (const event of streamGenerateContent({
        conversation_id: conversationId,
        user_id: userId,
        brief: confirmedBrief as unknown as Record<string, unknown>,
        products: selectedProducts as unknown as Array<Record<string, unknown>>,
        generate_images: imageGenerationEnabled,
      }, signal)) {
        
        if (event.type === 'heartbeat') {
          const statusMessage = (event.content as string) || 'Generating content...';
          const elapsed = (event as { elapsed?: number }).elapsed || 0;
          setGenerationStatus(elapsed > 0 ? `${statusMessage} (${elapsed}s)` : statusMessage);
        } else if (event.type === 'agent_response' && event.is_final) {
          let result: Record<string, unknown> | undefined = event.content as unknown as Record<string, unknown>;
          if (typeof event.content === 'string') {
            try {
              result = JSON.parse(event.content);
            } catch {
              result = {};
            }
          }
          
          let imageUrl = result?.image_url as string | undefined;
          
          // Convert blob URLs to proxy URLs
          if (imageUrl && imageUrl.includes('blob.core.windows.net')) {
            const parts = imageUrl.split('/');
            const filename = parts[parts.length - 1];
            const convId = parts[parts.length - 2];
            imageUrl = `/api/images/${convId}/${filename}`;
          }
          
          // Parse text_content - it may be a JSON string from backend
          let textContent: Record<string, unknown> | undefined;
          const rawTextContent = result?.text_content;
          if (typeof rawTextContent === 'string') {
            try {
              textContent = JSON.parse(rawTextContent);
            } catch {
              console.error('Failed to parse text_content JSON string');
              textContent = undefined;
            }
          } else {
            textContent = rawTextContent as Record<string, unknown> | undefined;
          }
          
          const generatedContent: GeneratedContent = {
            text_content: textContent ? {
              headline: textContent.headline as string | undefined,
              body: textContent.body as string | undefined,
              cta_text: textContent.cta as string | undefined,
            } : {
              headline: result?.headline as string | undefined,
              body: result?.body as string | undefined,
              cta_text: result?.cta as string | undefined,
            },
            image_content: imageUrl ? {
              image_url: imageUrl,
              prompt_used: result?.image_prompt as string | undefined,
              alt_text: (result?.image_revised_prompt as string) || 'Generated marketing image',
            } : undefined,
            violations: (result?.violations as unknown as GeneratedContent['violations']) || [],
            requires_modification: (result?.requires_modification as boolean) || false,
          };
          
          setGeneratedContent(generatedContent);
        } else if (event.type === 'error') {
          throw new Error(event.content || 'Generation failed');
        }
      }
      
      setGenerationStatus('');
    } catch (error) {
      // Check if this was a user-initiated cancellation
      if (error instanceof Error && error.name === 'AbortError') {
        console.log('Content generation cancelled by user');
        const cancelMessage: ChatMessage = {
          id: uuidv4(),
          role: 'assistant',
          content: 'Content generation stopped.',
          timestamp: new Date().toISOString(),
        };
        setMessages(prev => [...prev, cancelMessage]);
      } else {
        console.error('Error generating content:', error);
        const errorMessage: ChatMessage = {
          id: uuidv4(),
          role: 'assistant',
          content: 'Sorry, there was an error generating content. Please try again.',
          timestamp: new Date().toISOString(),
        };
        setMessages(prev => [...prev, errorMessage]);
      }
    } finally {
      setIsLoading(false);
      setGenerationStatus('');
      abortControllerRef.current = null;
    }
  }, [confirmedBrief, selectedProducts, conversationId, userId, imageGenerationEnabled]);

  return (
    <div className="app-container">
      {/* Header */}
      <header style={{ 
        display: 'flex', 
        alignItems: 'center', 
        justifyContent: 'space-between',
        padding: 'clamp(8px, 1.5vw, 12px) clamp(16px, 3vw, 24px)',
        borderBottom: `1px solid ${tokens.colorNeutralStroke2}`,
        backgroundColor: tokens.colorNeutralBackground1,
        flexShrink: 0,
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 'clamp(8px, 1.5vw, 10px)' }}>
          <img src={ContosoLogo} alt="Contoso" width="28" height="28" />
          <Text weight="semibold" size={500} style={{ color: tokens.colorNeutralForeground1, fontSize: 'clamp(16px, 2.5vw, 20px)' }}>
            Contoso
          </Text>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <Tooltip content={showChatHistory ? 'Hide chat history' : 'Show chat history'} relationship="label">
            <Button
              appearance="subtle"
              icon={showChatHistory ? <History24Filled /> : <History24Regular />}
              onClick={() => setShowChatHistory(!showChatHistory)}
              aria-label={showChatHistory ? 'Hide chat history' : 'Show chat history'}
            />
          </Tooltip>
          <Avatar 
            name={userName || undefined}
            color="colorful"
            size={36}
          />
        </div>
      </header>
      
      {/* Main Content */}
      <div className="main-content">
        {/* Chat Panel - main area */}
        <div className="chat-panel">
          <ChatPanel
            messages={messages}
            onSendMessage={handleSendMessage}
            isLoading={isLoading}
            generationStatus={generationStatus}
            onStopGeneration={handleStopGeneration}
            pendingBrief={pendingBrief}
            confirmedBrief={confirmedBrief}
            generatedContent={generatedContent}
            selectedProducts={selectedProducts}
            availableProducts={availableProducts}
            onBriefConfirm={handleBriefConfirm}
            onBriefCancel={handleBriefCancel}
            onGenerateContent={handleGenerateContent}
            onRegenerateContent={handleGenerateContent}
            onProductsStartOver={handleProductsStartOver}
            onProductSelect={handleProductSelect}
            imageGenerationEnabled={imageGenerationEnabled}
            onNewConversation={handleNewConversation}
          />
        </div>
        
        {/* Chat History Sidebar - RIGHT side */}
        {showChatHistory && (
          <div className="history-panel">
            <ChatHistory
            currentConversationId={conversationId}
            currentConversationTitle={conversationTitle}
            currentMessages={messages}
            onSelectConversation={handleSelectConversation}
            onNewConversation={handleNewConversation}
              refreshTrigger={historyRefreshTrigger}
              isGenerating={isLoading}
            />
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
