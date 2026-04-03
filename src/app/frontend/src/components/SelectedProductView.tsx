import {
  Text,
  Badge,
  tokens,
} from '@fluentui/react-components';
import {
  Checkmark20Regular,
  Box20Regular,
} from '@fluentui/react-icons';
import type { Product } from '../types';

interface SelectedProductViewProps {
  products: Product[];
}

export function SelectedProductView({ products }: SelectedProductViewProps) {
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
          <div 
            key={product.sku || index} 
            style={{ 
              display: 'flex',
              flexDirection: 'row',
              alignItems: 'center',
              gap: '12px',
              padding: '12px',
              backgroundColor: tokens.colorNeutralBackground1,
              borderRadius: '8px',
              border: `1px solid ${tokens.colorNeutralStroke2}`,
            }}
          >
            {product.image_url ? (
              <img
                src={product.image_url}
                alt={product.product_name}
                style={{
                  width: '56px',
                  height: '56px',
                  objectFit: 'cover',
                  borderRadius: '6px',
                  border: `1px solid ${tokens.colorNeutralStroke2}`,
                  flexShrink: 0,
                }}
              />
            ) : (
              <div 
                style={{
                  width: '56px',
                  height: '56px',
                  borderRadius: '6px',
                  backgroundColor: tokens.colorNeutralBackground3,
                  border: `1px solid ${tokens.colorNeutralStroke2}`,
                  flexShrink: 0,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                }}
              >
                <Box20Regular style={{ color: tokens.colorNeutralForeground3 }} />
              </div>
            )}
            
            <div style={{ flex: 1, minWidth: 0 }}>
              <Text 
                weight="semibold" 
                size={300}
                style={{
                  display: 'block',
                  color: tokens.colorNeutralForeground1,
                  marginBottom: '2px',
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
                }}
              >
                {product.tags || product.description || 'soft white, airy, minimal, fresh'}
              </Text>
              <Text 
                weight="semibold" 
                size={200}
                style={{ 
                  display: 'block',
                  color: tokens.colorNeutralForeground1,
                  marginTop: '2px',
                }}
              >
                ${product.price?.toFixed(2) || '59.95'} USD
              </Text>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
