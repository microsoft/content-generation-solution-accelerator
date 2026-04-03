import { memo, useMemo, useCallback } from 'react';
import {
  Button,
  Text,
  tokens,
} from '@fluentui/react-components';
import {
  Sparkle20Regular,
} from '@fluentui/react-icons';
import type { Product } from '../types';
import { AI_DISCLAIMER } from '../utils';
import { ProductCard } from './ProductCard';

interface ProductReviewProps {
  products: Product[];
  onConfirm: () => void;
  isAwaitingResponse?: boolean;
  availableProducts?: Product[];
  onProductSelect?: (product: Product) => void;
  disabled?: boolean;
}

export const ProductReview = memo(function ProductReview({
  products,
  onConfirm,
  isAwaitingResponse = false,
  availableProducts = [],
  onProductSelect,
  disabled = false,
}: ProductReviewProps) {
  const displayProducts = useMemo(
    () => availableProducts.length > 0 ? availableProducts : products,
    [availableProducts, products],
  );
  const selectedProductIds = useMemo(
    () => new Set(products.map(p => p.sku || p.product_name)),
    [products],
  );

  const isProductSelected = useCallback((product: Product): boolean => {
    return selectedProductIds.has(product.sku || product.product_name);
  }, [selectedProductIds]);

  const handleProductClick = useCallback((product: Product) => {
    if (onProductSelect) {
      onProductSelect(product);
    }
  }, [onProductSelect]);

  return (
    <div className="message assistant" style={{ 
      width: '100%',
      alignSelf: 'flex-start',
      backgroundColor: tokens.colorNeutralBackground3,
      padding: '12px 16px',
      borderRadius: '8px',
      margin: '16px 0 0 0',
    }}>
      <div style={{ marginBottom: '16px' }}>
        <Text size={300} style={{ color: tokens.colorNeutralForeground1 }}>
          Here is the list of available paints:
        </Text>
      </div>

      {displayProducts.length > 0 ? (
        <div className="product-grid" style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(2, 1fr)',
          gap: '16px',
          marginBottom: '16px',
          maxHeight: '500px',
          overflowY: 'auto',
        }}>
          {displayProducts.map((product, index) => (
            <ProductCard
              key={product.sku || index}
              product={product}
              isSelected={isProductSelected(product)}
              onClick={() => handleProductClick(product)}
              disabled={disabled}
            />
          ))}
        </div>
      ) : (
        <div style={{
          padding: '24px',
          textAlign: 'center',
          backgroundColor: tokens.colorNeutralBackground2,
          borderRadius: '8px',
          marginBottom: '16px',
        }}>
          <Text size={200} style={{ color: tokens.colorNeutralForeground3 }}>
            No products available.
          </Text>
        </div>
      )}

      {displayProducts.length > 0 && (
        <div style={{ 
          display: 'flex',
          gap: '8px',
          flexWrap: 'wrap',
          marginTop: '16px',
        }}>
          <Button
            appearance="primary"
            icon={<Sparkle20Regular />}
            onClick={onConfirm}
            disabled={isAwaitingResponse || products.length === 0}
            size="small"
          >
            Generate Content
          </Button>
          {products.length === 0 && (
            <Text size={200} style={{ color: tokens.colorNeutralForeground3, alignSelf: 'center' }}>
              Select a product to continue
            </Text>
          )}
        </div>
      )}

      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginTop: '12px',
        paddingTop: '8px',
      }}>
        <Text size={100} style={{ color: tokens.colorNeutralForeground4 }}>
          {AI_DISCLAIMER}
        </Text>
      </div>
    </div>
  );
});
ProductReview.displayName = 'ProductReview';
