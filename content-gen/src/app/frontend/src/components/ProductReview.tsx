import {
  Button,
  Text,
  tokens,
} from '@fluentui/react-components';
import {
  Sparkle20Regular,
  Box20Regular,
} from '@fluentui/react-icons';
import type { Product } from '../types';

interface ProductReviewProps {
  products: Product[];
  onConfirm: () => void;
  onStartOver: () => void;
  isAwaitingResponse?: boolean;
  availableProducts?: Product[];
  onProductSelect?: (product: Product) => void;
  disabled?: boolean;
}

export function ProductReview({
  products,
  onConfirm,
  onStartOver: _onStartOver,
  isAwaitingResponse = false,
  availableProducts = [],
  onProductSelect,
  disabled = false,
}: ProductReviewProps) {
  const displayProducts = availableProducts.length > 0 ? availableProducts : products;
  const selectedProductIds = new Set(products.map(p => p.sku || p.product_name));

  const isProductSelected = (product: Product): boolean => {
    return selectedProductIds.has(product.sku || product.product_name);
  };

  const handleProductClick = (product: Product) => {
    if (onProductSelect) {
      onProductSelect(product);
    }
  };

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
            <ProductCardGrid
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
          AI-generated content may be incorrect
        </Text>
      </div>
    </div>
  );
}

interface ProductCardGridProps {
  product: Product;
  isSelected: boolean;
  onClick: () => void;
  disabled?: boolean;
}

function ProductCardGrid({ product, isSelected, onClick, disabled = false }: ProductCardGridProps) {
  return (
    <div 
      className={`product-card ${isSelected ? 'selected' : ''} ${disabled ? 'disabled' : ''}`}
      onClick={disabled ? undefined : onClick}
      style={{
        display: 'flex',
        flexDirection: 'row',
        alignItems: 'center',
        gap: '16px',
        padding: '16px',
        borderRadius: '8px',
        border: isSelected ? `2px solid ${tokens.colorBrandStroke1}` : `1px dashed ${tokens.colorNeutralStroke2}`,
        backgroundColor: isSelected ? tokens.colorBrandBackground2 : tokens.colorNeutralBackground1,
        cursor: disabled ? 'not-allowed' : 'pointer',
        opacity: disabled ? 0.6 : 1,
        transition: 'all 0.15s ease-in-out',
        pointerEvents: disabled ? 'none' : 'auto',
      }}
    >
      {product.image_url ? (
        <img
          src={product.image_url}
          alt={product.product_name}
          style={{
            width: '80px',
            height: '80px',
            objectFit: 'cover',
            borderRadius: '8px',
            border: `1px solid ${tokens.colorNeutralStroke2}`,
            flexShrink: 0,
          }}
        />
      ) : (
        <div 
          style={{
            width: '80px',
            height: '80px',
            borderRadius: '8px',
            backgroundColor: tokens.colorNeutralBackground3,
            border: `1px solid ${tokens.colorNeutralStroke2}`,
            flexShrink: 0,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          <Box20Regular style={{ color: tokens.colorNeutralForeground3, fontSize: '24px' }} />
        </div>
      )}
      
      <div className="product-info" style={{ flex: 1, minWidth: 0 }}>
        <Text 
          weight="semibold" 
          size={400}
          style={{ 
            display: 'block',
            color: tokens.colorNeutralForeground1,
            marginBottom: '4px',
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
            marginBottom: '4px',
          }}
        >
          {product.tags || product.description || 'soft white, airy, minimal, fresh'}
        </Text>
        <Text 
          weight="semibold" 
          size={300}
          style={{ 
            display: 'block',
            color: tokens.colorNeutralForeground1,
          }}
        >
          ${product.price?.toFixed(2) || '59.95'} USD
        </Text>
      </div>
    </div>
  );
}
