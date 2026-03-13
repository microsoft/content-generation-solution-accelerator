import { memo } from 'react';
import {
  Button,
  Text,
  Tooltip,
  tokens,
} from '@fluentui/react-components';
import { ArrowDownload20Regular } from '@fluentui/react-icons';

export interface ImagePreviewCardProps {
  imageUrl: string;
  altText?: string;
  productName?: string;
  tagline?: string;
  isSmall?: boolean;
  onDownload: () => void;
}

/**
 * Image preview with download button overlay and a product-name / tagline
 * text banner below the image.
 */
export const ImagePreviewCard = memo(function ImagePreviewCard({
  imageUrl,
  altText = 'Generated marketing image',
  productName = 'Your Product',
  tagline,
  isSmall = false,
  onDownload,
}: ImagePreviewCardProps) {
  return (
    <div
      style={{
        borderRadius: '8px',
        overflow: 'hidden',
        marginBottom: '16px',
        maxWidth: isSmall ? '100%' : '500px',
        backgroundColor: tokens.colorNeutralBackground1,
        border: `1px solid ${tokens.colorNeutralStroke2}`,
      }}
    >
      {/* Image container */}
      <div style={{ position: 'relative' }}>
        <img
          src={imageUrl}
          alt={altText}
          style={{ width: '100%', height: 'auto', display: 'block' }}
        />

        <Tooltip content="Download image with banner" relationship="label">
          <Button
            appearance="subtle"
            icon={<ArrowDownload20Regular />}
            size="small"
            onClick={onDownload}
            style={{
              position: 'absolute',
              bottom: '8px',
              right: '8px',
              backgroundColor: 'rgba(255,255,255,0.9)',
              minWidth: '32px',
            }}
          />
        </Tooltip>
      </div>

      {/* Text banner below image */}
      <div
        style={{
          padding: '12px 16px',
          backgroundColor: tokens.colorNeutralBackground1,
          borderTop: `1px solid ${tokens.colorNeutralStroke2}`,
        }}
      >
        <Text
          size={400}
          weight="semibold"
          style={{
            color: tokens.colorNeutralForeground1,
            display: 'block',
            fontFamily: 'Georgia, serif',
            marginBottom: '4px',
          }}
        >
          {productName}
        </Text>
        {tagline && (
          <Text
            size={200}
            style={{ color: tokens.colorNeutralForeground3, fontStyle: 'italic' }}
          >
            {tagline}
          </Text>
        )}
      </div>
    </div>
  );
});
ImagePreviewCard.displayName = 'ImagePreviewCard';
