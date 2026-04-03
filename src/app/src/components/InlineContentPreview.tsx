import { memo, useCallback, useMemo } from 'react';
import {
  Text,
  Divider,
  tokens,
} from '@fluentui/react-components';
import { ShieldError20Regular } from '@fluentui/react-icons';
import type { GeneratedContent, Product } from '../types';
import { useWindowSize, useCopyToClipboard } from '../hooks';
import { isContentFilterError, getErrorMessage, downloadImage } from '../utils';
import { ImagePreviewCard } from './ImagePreviewCard';
import { ComplianceSection } from './ComplianceSection';

interface InlineContentPreviewProps {
  content: GeneratedContent;
  onRegenerate: () => void;
  isLoading?: boolean;
  selectedProduct?: Product;
  imageGenerationEnabled?: boolean;
}

export const InlineContentPreview = memo(function InlineContentPreview({ 
  content, 
  onRegenerate, 
  isLoading, 
  selectedProduct, 
  imageGenerationEnabled = true,
}: InlineContentPreviewProps) {
  const { text_content, image_content, violations, requires_modification, error, image_error, text_error } = content;
  const { copied, copy } = useCopyToClipboard();
  const windowWidth = useWindowSize();
  
  const isSmall = windowWidth < 768;

  const handleCopyText = useCallback(() => {
    const textToCopy = [
      text_content?.headline && `✨ ${text_content.headline} ✨`,
      text_content?.body,
      text_content?.tagline,
    ].filter(Boolean).join('\n\n');
    copy(textToCopy);
  }, [text_content, copy]);

  const handleDownloadImage = useCallback(() => {
    if (!image_content?.image_url) return;
    downloadImage(
      image_content.image_url,
      selectedProduct?.product_name || text_content?.headline || 'Your Product',
      text_content?.tagline,
    );
  }, [image_content, selectedProduct, text_content]);

  // Get product display name
  const productDisplayName = useMemo(() => {
    if (selectedProduct) {
      return selectedProduct.product_name;
    }
    return text_content?.headline || 'Your Content';
  }, [selectedProduct, text_content?.headline]);

  return (
    <div className="message assistant" style={{ 
      width: '100%',
      alignSelf: 'flex-start',
      backgroundColor: tokens.colorNeutralBackground3,
      padding: '12px 16px',
      borderRadius: '8px',
      margin: '16px 0 0 0',
    }}>
      {/* Selection confirmation */}
      {selectedProduct && (
        <Text size={200} style={{ 
          color: tokens.colorNeutralForeground3, 
          display: 'block',
          marginBottom: '8px',
        }}>
          You selected "{selectedProduct.product_name}". Here's what I've created – let me know if you need anything changed.
        </Text>
      )}

      {/* Sparkle Headline - Figma style */}
      {text_content?.headline && (
        <Text 
          weight="semibold" 
          size={400}
          style={{ 
            display: 'block',
            marginBottom: '16px',
            color: tokens.colorNeutralForeground1,
            fontSize: '18px',
          }}
        >
          ✨ Discover the serene elegance of {productDisplayName}.
        </Text>
      )}

      {/* Body Copy */}
      {text_content?.body && (
        <Text 
          size={300}
          style={{ 
            display: 'block',
            marginBottom: '16px',
            lineHeight: '1.6',
            color: tokens.colorNeutralForeground2,
          }}
        >
          {text_content.body}
        </Text>
      )}

      {/* Hashtags */}
      {text_content?.tagline && (
        <Text 
          size={200}
          style={{ 
            display: 'block',
            marginBottom: '16px',
            lineHeight: '1.8',
            color: tokens.colorBrandForeground1,
          }}
        >
          {text_content.tagline}
        </Text>
      )}

      {/* Error Banner */}
      {(error || text_error) && !violations.some(v => v.message.toLowerCase().includes('filter')) && (
        <div style={{ 
          padding: '12px 16px', 
          backgroundColor: isContentFilterError(error || text_error) ? '#fef3f2' : '#fef9ee',
          border: `1px solid ${isContentFilterError(error || text_error) ? '#fecaca' : '#fde68a'}`,
          borderRadius: '8px',
          marginBottom: '16px',
          display: 'flex',
          alignItems: 'flex-start',
          gap: '12px'
        }}>
          <ShieldError20Regular style={{ 
            color: isContentFilterError(error || text_error) ? '#dc2626' : '#d97706',
            flexShrink: 0,
            marginTop: '2px',
          }} />
          <div>
            <Text weight="semibold" size={300} block style={{ 
              color: isContentFilterError(error || text_error) ? '#b91c1c' : '#92400e',
              marginBottom: '4px',
            }}>
              {getErrorMessage(error || text_error).title}
            </Text>
            <Text size={200} style={{ color: tokens.colorNeutralForeground3 }}>
              {getErrorMessage(error || text_error).description}
            </Text>
          </div>
        </div>
      )}

      {/* Image Preview */}
      {imageGenerationEnabled && image_content?.image_url && (
        <ImagePreviewCard
          imageUrl={image_content.image_url}
          altText={image_content.alt_text}
          productName={selectedProduct?.product_name || text_content?.headline || 'Your Product'}
          tagline={text_content?.tagline}
          isSmall={isSmall}
          onDownload={handleDownloadImage}
        />
      )}

      {/* Image Error State */}
      {imageGenerationEnabled && !image_content?.image_url && (image_error || error) && (
        <div style={{ 
          borderRadius: '8px',
          padding: '32px',
          backgroundColor: isContentFilterError(image_error || error) ? '#fef3f2' : '#fef9ee',
          border: `1px solid ${isContentFilterError(image_error || error) ? '#fecaca' : '#fde68a'}`,
          marginBottom: '16px',
          textAlign: 'center',
        }}>
          <ShieldError20Regular style={{ 
            fontSize: '32px', 
            color: isContentFilterError(image_error || error) ? '#dc2626' : '#d97706',
            marginBottom: '8px',
          }} />
          <Text weight="semibold" size={300} block style={{ 
            color: isContentFilterError(image_error || error) ? '#b91c1c' : '#92400e',
          }}>
            {getErrorMessage(image_error || error).title}
          </Text>
          <Text size={200} style={{ color: tokens.colorNeutralForeground3, marginTop: '4px' }}>
            Click Regenerate to try again
          </Text>
        </div>
      )}

      <Divider style={{ margin: '16px 0' }} />

      {/* Compliance + Footer + Accordion */}
      <ComplianceSection
        violations={violations}
        requiresModification={requires_modification}
        onCopyText={handleCopyText}
        onRegenerate={onRegenerate}
        isLoading={isLoading}
        copied={copied}
      />
    </div>
  );
});
InlineContentPreview.displayName = 'InlineContentPreview';
