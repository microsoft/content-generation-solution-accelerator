import { memo } from 'react';
import {
  Badge,
  tokens,
} from '@fluentui/react-components';
import {
  Checkmark20Regular,
} from '@fluentui/react-icons';
import type { Product } from '../types';
import { ProductCard } from './ProductCard';

interface SelectedProductViewProps {
  products: Product[];
}

export const SelectedProductView = memo(function SelectedProductView({ products }: SelectedProductViewProps) {
  if (products.length === 0) return null;

  return (
    <div className="message assistant" style={{ 
      width: '100%',
      alignSelf: 'flex-start',
      backgroundColor: tokens.colorNeutralBackground3,
      padding: '12px 16px',
      borderRadius: '8px',
      margin: '16px 0 0 0',
      opacity: 0.85,
    }}>
      <div style={{ 
        display: 'flex', 
        alignItems: 'center', 
        gap: '8px', 
        marginBottom: '12px' 
      }}>
        <Badge 
          appearance="filled" 
          size="small" 
          color="success"
          icon={<Checkmark20Regular />}
        >
          Products Selected
        </Badge>
      </div>
      
      <div style={{ 
        display: 'grid',
        gridTemplateColumns: 'repeat(2, 1fr)',
        gap: '12px',
        maxHeight: '300px',
        overflowY: 'auto',
      }}>
        {products.map((product, index) => (
          <ProductCard
            key={product.sku || index}
            product={product}
            size="compact"
          />
        ))}
      </div>
    </div>
  );
});
SelectedProductView.displayName = 'SelectedProductView';
