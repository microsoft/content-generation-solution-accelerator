import { memo } from 'react';
import {
  Text,
  tokens,
} from '@fluentui/react-components';
import { Box20Regular } from '@fluentui/react-icons';
import type { Product } from '../types';

export interface ProductCardProps {
  product: Product;
  /** Visual size variant — "normal" for product review grid, "compact" for selected-product view. */
  size?: 'normal' | 'compact';
  /** Whether the card is currently selected (shows brand border). */
  isSelected?: boolean;
  /** Click handler. Omit for read-only cards. */
  onClick?: () => void;
  disabled?: boolean;
}

/**
 * Reusable product card with image/placeholder, name, tags and price.
 * Used by both ProductReview (selectable) and SelectedProductView (read-only).
 */
export const ProductCard = memo(function ProductCard({
  product,
  size = 'normal',
  isSelected = false,
  onClick,
  disabled = false,
}: ProductCardProps) {
  const isCompact = size === 'compact';
  const imgSize = isCompact ? 56 : 80;
  const isInteractive = !!onClick && !disabled;

  return (
    <div
      className={`product-card ${isSelected ? 'selected' : ''} ${disabled ? 'disabled' : ''}`}
      onClick={isInteractive ? onClick : undefined}
      style={{
        display: 'flex',
        flexDirection: 'row',
        alignItems: 'center',
        gap: isCompact ? '12px' : '16px',
        padding: isCompact ? '12px' : '16px',
        borderRadius: '8px',
        border: isSelected
          ? `2px solid ${tokens.colorBrandStroke1}`
          : `1px ${isInteractive ? 'dashed' : 'solid'} ${tokens.colorNeutralStroke2}`,
        backgroundColor: isSelected
          ? tokens.colorBrandBackground2
          : tokens.colorNeutralBackground1,
        cursor: isInteractive ? 'pointer' : disabled ? 'not-allowed' : 'default',
        opacity: disabled ? 0.6 : 1,
        transition: 'all 0.15s ease-in-out',
        pointerEvents: disabled ? 'none' : 'auto',
      }}
    >
      {/* Image or placeholder */}
      {product.image_url ? (
        <img
          src={product.image_url}
          alt={product.product_name}
          style={{
            width: `${imgSize}px`,
            height: `${imgSize}px`,
            objectFit: 'cover',
            borderRadius: isCompact ? '6px' : '8px',
            border: `1px solid ${tokens.colorNeutralStroke2}`,
            flexShrink: 0,
          }}
        />
      ) : (
        <div
          style={{
            width: `${imgSize}px`,
            height: `${imgSize}px`,
            borderRadius: isCompact ? '6px' : '8px',
            backgroundColor: tokens.colorNeutralBackground3,
            border: `1px solid ${tokens.colorNeutralStroke2}`,
            flexShrink: 0,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          <Box20Regular
            style={{
              color: tokens.colorNeutralForeground3,
              fontSize: isCompact ? undefined : '24px',
            }}
          />
        </div>
      )}

      {/* Product info */}
      <div className="product-info" style={{ flex: 1, minWidth: 0 }}>
        <Text
          weight="semibold"
          size={isCompact ? 300 : 400}
          style={{
            display: 'block',
            color: tokens.colorNeutralForeground1,
            marginBottom: isCompact ? '2px' : '4px',
          }}
        >
          {product.product_name}
        </Text>
        <Text
          size={200}
          style={{
            display: 'block',
            color: tokens.colorNeutralForeground3,
            overflow: 'hidden',
            textOverflow: 'ellipsis',
            whiteSpace: 'nowrap',
            marginBottom: isCompact ? '2px' : '4px',
          }}
        >
          {product.tags || product.description || 'soft white, airy, minimal, fresh'}
        </Text>
        <Text
          weight="semibold"
          size={isCompact ? 200 : 300}
          style={{
            display: 'block',
            color: tokens.colorNeutralForeground1,
            ...(isCompact ? { marginTop: '2px' } : {}),
          }}
        >
          ${product.price?.toFixed(2) || '59.95'} USD
        </Text>
      </div>
    </div>
  );
});
ProductCard.displayName = 'ProductCard';
