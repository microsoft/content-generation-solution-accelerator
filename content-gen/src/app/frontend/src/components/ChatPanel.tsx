import { useState, useRef, useEffect } from 'react';
import {
  Button,
  Text,
  Badge,
  tokens,
  Tooltip,
} from '@fluentui/react-components';
import {
  Send20Regular,
  Stop24Regular,
  Add20Regular,
  Copy20Regular,
} from '@fluentui/react-icons';
import ReactMarkdown from 'react-markdown';
import type { ChatMessage, CreativeBrief, Product, GeneratedContent } from '../types';
import { BriefReview } from './BriefReview';
import { ConfirmedBriefView } from './ConfirmedBriefView';
import { SelectedProductView } from './SelectedProductView';
import { ProductReview } from './ProductReview';
import { InlineContentPreview } from './InlineContentPreview';
import { WelcomeCard } from './WelcomeCard';

interface ChatPanelProps {
  messages: ChatMessage[];
  onSendMessage: (message: string) => void;
  isLoading: boolean;
  generationStatus?: string;
  onStopGeneration?: () => void;
  // Inline component props
  pendingBrief?: CreativeBrief | null;
  confirmedBrief?: CreativeBrief | null;
  generatedContent?: GeneratedContent | null;
  selectedProducts?: Product[];
  availableProducts?: Product[];
  onBriefConfirm?: () => void;
  onBriefCancel?: () => void;
  onGenerateContent?: () => void;
  onRegenerateContent?: () => void;
  onProductsStartOver?: () => void;
  onProductSelect?: (product: Product) => void;
  // Feature flags
  imageGenerationEnabled?: boolean;
  // New chat
  onNewConversation?: () => void;
}

export function ChatPanel({ 
  messages, 
  onSendMessage, 
  isLoading,
  generationStatus,
  onStopGeneration,
  pendingBrief,
  confirmedBrief,
  generatedContent,
  selectedProducts = [],
  availableProducts = [],
  onBriefConfirm,
  onBriefCancel,
  onGenerateContent,
  onRegenerateContent,
  onProductsStartOver,
  onProductSelect,
  imageGenerationEnabled = true,
  onNewConversation,
}: ChatPanelProps) {
  const [inputValue, setInputValue] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const messagesContainerRef = useRef<HTMLDivElement>(null);
  const inputContainerRef = useRef<HTMLDivElement>(null);

  // Scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, pendingBrief, confirmedBrief, generatedContent, isLoading, generationStatus]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (inputValue.trim() && !isLoading) {
      onSendMessage(inputValue.trim());
      setInputValue('');
    }
  };

  // Determine if we should show inline components
  const showBriefReview = pendingBrief && onBriefConfirm && onBriefCancel;
  const showProductReview = confirmedBrief && !generatedContent && onGenerateContent;
  const showContentPreview = generatedContent && onRegenerateContent;
  const showWelcome = messages.length === 0 && !showBriefReview && !showProductReview && !showContentPreview;

  // Handle suggestion click from welcome card
  const handleSuggestionClick = (prompt: string) => {
    setInputValue(prompt);
  };

  return (
    <div className="chat-container">
      {/* Messages Area */}
      <div 
        className="messages"
        ref={messagesContainerRef}
        style={{ 
          flex: 1, 
          overflowY: 'auto', 
          overflowX: 'hidden',
          padding: '8px 8px',
          display: 'flex',
          flexDirection: 'column',
          gap: '12px',
          minHeight: 0,
          position: 'relative',
        }}
      >
        {showWelcome ? (
          <WelcomeCard onSuggestionClick={handleSuggestionClick} currentInput={inputValue} />
        ) : (
          <>
            {messages.map((message) => (
              <MessageBubble key={message.id} message={message} />
            ))}
            
            {/* Brief Review - Read Only with Conversational Prompts */}
            {showBriefReview && (
              <BriefReview
                brief={pendingBrief}
                onConfirm={onBriefConfirm}
                onStartOver={onBriefCancel}
                isAwaitingResponse={isLoading}
              />
            )}
            
            {/* Confirmed Brief View - Persistent read-only view */}
            {confirmedBrief && !pendingBrief && (
              <ConfirmedBriefView brief={confirmedBrief} />
            )}
            
            {/* Selected Product View - Persistent read-only view after content generation */}
            {generatedContent && selectedProducts.length > 0 && (
              <SelectedProductView products={selectedProducts} />
            )}
            
            {/* Product Review - Conversational Product Selection */}
            {showProductReview && (
              <ProductReview
                products={selectedProducts}
                availableProducts={availableProducts}
                onConfirm={onGenerateContent}
                onStartOver={onProductsStartOver || (() => {})}
                isAwaitingResponse={isLoading}
                onProductSelect={onProductSelect}
                disabled={isLoading}
              />
            )}
            
            {/* Inline Content Preview */}
            {showContentPreview && (
              <InlineContentPreview
                content={generatedContent}
                onRegenerate={onRegenerateContent}
                isLoading={isLoading}
                selectedProduct={selectedProducts.length > 0 ? selectedProducts[0] : undefined}
                imageGenerationEnabled={imageGenerationEnabled}
              />
            )}
            
            {/* Loading/Typing Indicator - Coral Style */}
            {isLoading && (
              <div className="typing-indicator" style={{
                display: 'flex',
                alignItems: 'center',
                gap: '12px',
                padding: '12px 16px',
                backgroundColor: tokens.colorNeutralBackground3,
                borderRadius: '8px',
                alignSelf: 'flex-start',
                width: '100%',
              }}>
                <div className="thinking-dots">
                  <span style={{
                    display: 'inline-flex',
                    gap: '4px',
                    alignItems: 'center',
                  }}>
                    <span className="dot" style={{
                      width: '8px',
                      height: '8px',
                      borderRadius: '50%',
                      backgroundColor: tokens.colorBrandBackground,
                      animation: 'pulse 1.4s infinite ease-in-out',
                      animationDelay: '0s',
                    }} />
                    <span className="dot" style={{
                      width: '8px',
                      height: '8px',
                      borderRadius: '50%',
                      backgroundColor: tokens.colorBrandBackground,
                      animation: 'pulse 1.4s infinite ease-in-out',
                      animationDelay: '0.2s',
                    }} />
                    <span className="dot" style={{
                      width: '8px',
                      height: '8px',
                      borderRadius: '50%',
                      backgroundColor: tokens.colorBrandBackground,
                      animation: 'pulse 1.4s infinite ease-in-out',
                      animationDelay: '0.4s',
                    }} />
                  </span>
                </div>
                <Text size={300} style={{ color: tokens.colorNeutralForeground2 }}>
                  {generationStatus || 'Thinking...'}
                </Text>
                {onStopGeneration && (
                  <Tooltip content="Stop generation" relationship="label">
                    <Button
                      appearance="subtle"
                      icon={<Stop24Regular />}
                      onClick={onStopGeneration}
                      size="small"
                      style={{ 
                        color: tokens.colorPaletteRedForeground1,
                        minWidth: '32px',
                        marginLeft: 'auto',
                      }}
                    >
                      Stop
                    </Button>
                  </Tooltip>
                )}
              </div>
            )}
          </>
        )}
        
        <div ref={messagesEndRef} />
      </div>

      {/* Input Area - Simple single-line like Figma */}
      <div 
        ref={inputContainerRef}
        style={{
          margin: '0 8px 8px 8px',
          position: 'relative',
        }}
      >
        {/* Input Box */}
        <div 
          style={{
            display: 'flex',
            alignItems: 'center',
            padding: '8px 12px',
            borderRadius: '4px',
            backgroundColor: tokens.colorNeutralBackground1,
            border: `1px solid ${tokens.colorNeutralStroke2}`,
          }}
        >
          <input
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                handleSubmit(e);
              }
            }}
            placeholder="Type a message"
            disabled={isLoading}
            style={{
              flex: 1,
              border: 'none',
              outline: 'none',
              backgroundColor: 'transparent',
              fontFamily: 'var(--fontFamilyBase)',
              fontSize: '14px',
              color: tokens.colorNeutralForeground1,
            }}
          />
          
          {/* Icons on the right */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '0px' }}>
            <Tooltip content="New chat" relationship="label">
              <Button
                appearance="subtle"
                icon={<Add20Regular />}
                size="small"
                onClick={onNewConversation}
                disabled={isLoading}
                style={{ 
                  minWidth: '32px',
                  height: '32px',
                  color: tokens.colorNeutralForeground3,
                }}
              />
            </Tooltip>
            
            {/* Vertical divider */}
            <div style={{
              width: '1px',
              height: '20px',
              backgroundColor: tokens.colorNeutralStroke2,
              margin: '0 4px',
            }} />
            
            <Button
              appearance="subtle"
              icon={<Send20Regular />}
              size="small"
              onClick={handleSubmit}
              disabled={!inputValue.trim() || isLoading}
              style={{ 
                minWidth: '32px',
                height: '32px',
                color: inputValue.trim() ? tokens.colorBrandForeground1 : tokens.colorNeutralForeground4,
              }}
            />
          </div>
        </div>
        
        {/* Disclaimer - Outside the input box */}
        <Text 
          size={100} 
          style={{ 
            display: 'block',
            marginTop: '8px',
            color: tokens.colorNeutralForeground4,
            fontSize: '12px',
          }}
        >
          AI generated content may be incorrect
        </Text>
      </div>
    </div>
  );
}

// Copy function for messages
const handleCopy = (text: string) => {
  navigator.clipboard.writeText(text).catch((err) => {
    console.error('Failed to copy text:', err);
  });
};

function MessageBubble({ message }: { message: ChatMessage }) {
  const isUser = message.role === 'user';
  const [copied, setCopied] = useState(false);

  const onCopy = () => {
    handleCopy(message.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };
  
  return (
    <div 
      className={`message ${isUser ? 'user' : 'assistant'}`}
      style={{ 
        display: 'inline-block',
        wordWrap: 'break-word',
        wordBreak: 'break-word',
        boxSizing: 'border-box',
        ...(isUser ? {
          backgroundColor: tokens.colorBrandBackground2,
          color: tokens.colorNeutralForeground1,
          alignSelf: 'flex-end',
          padding: '12px 16px',
          borderRadius: '8px',
          maxWidth: '80%',
        } : {
          backgroundColor: tokens.colorNeutralBackground3,
          color: tokens.colorNeutralForeground1,
          alignSelf: 'flex-start',
          margin: '16px 0 0 0',
          padding: '12px 16px',
          borderRadius: '8px',
          width: '100%',
        }),
      }}
    >
      {/* Agent badge for assistant messages */}
      {!isUser && message.agent && (
        <Badge appearance="outline" size="small" style={{ marginBottom: '8px' }}>
          {message.agent}
        </Badge>
      )}
      
      {/* Message content with markdown */}
      <div className="message-content" style={{ 
        display: 'flex',
        flexDirection: 'column',
        whiteSpace: 'pre-wrap',
        width: '100%',
      }}>
        <ReactMarkdown>
          {message.content}
        </ReactMarkdown>

        {/* Footer for assistant messages - Coral style */}
        {!isUser && (
          <div className="assistant-footer" style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            marginTop: '12px',
          }}>
            <Text size={100} style={{ 
              color: tokens.colorNeutralForeground4,
              fontSize: '11px',
            }}>
              AI-generated content may be incorrect
            </Text>
            
            <div className="assistant-actions" style={{
              display: 'flex',
              gap: '4px',
            }}>
              <Tooltip content={copied ? 'Copied!' : 'Copy'} relationship="label">
                <Button
                  appearance="subtle"
                  icon={<Copy20Regular />}
                  size="small"
                  onClick={onCopy}
                  style={{ 
                    minWidth: '28px', 
                    height: '28px',
                    color: tokens.colorNeutralForeground3,
                  }}
                />
              </Tooltip>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
