import { memo } from 'react';
import { AI_DISCLAIMER } from '../utils';
import {
  Text,
  Badge,
  Button,
  Tooltip,
  Accordion,
  AccordionItem,
  AccordionHeader,
  AccordionPanel,
  tokens,
} from '@fluentui/react-components';
import {
  ArrowSync20Regular,
  CheckmarkCircle20Regular,
  Warning20Regular,
  Info20Regular,
  ErrorCircle20Regular,
  Copy20Regular,
} from '@fluentui/react-icons';
import type { ComplianceViolation } from '../types';
import { ViolationCard } from './ViolationCard';

export interface ComplianceSectionProps {
  violations: ComplianceViolation[];
  requiresModification: boolean;
  /** Callback to copy generated text. */
  onCopyText: () => void;
  /** Callback to regenerate content. */
  onRegenerate: () => void;
  /** Whether regeneration is in progress. */
  isLoading?: boolean;
  /** Whether the copy-text button shows "Copied!". */
  copied?: boolean;
}

/**
 * Compliance callout (action-needed / review-recommended), status footer
 * with badges and actions, and the collapsible violations accordion.
 */
export const ComplianceSection = memo(function ComplianceSection({
  violations,
  requiresModification,
  onCopyText,
  onRegenerate,
  isLoading,
  copied = false,
}: ComplianceSectionProps) {
  return (
    <>
      {/* User guidance callout */}
      {requiresModification ? (
        <div
          style={{
            padding: '12px 16px',
            backgroundColor: '#fde7e9',
            border: '1px solid #fecaca',
            borderRadius: '8px',
            marginBottom: '16px',
          }}
        >
          <Text size={200} style={{ color: '#b91c1c' }}>
            <strong>Action needed:</strong> This content has compliance issues that must be
            addressed before use. Please review the details in the Compliance Guidelines
            section below and regenerate with modifications, or manually edit the content to
            resolve the flagged items.
          </Text>
        </div>
      ) : violations.length > 0 ? (
        <div
          style={{
            padding: '12px 16px',
            backgroundColor: '#fff8e6',
            border: '1px solid #fde68a',
            borderRadius: '8px',
            marginBottom: '16px',
          }}
        >
          <Text size={200} style={{ color: '#92400e' }}>
            <strong>Optional review:</strong> This content is approved but has minor
            suggestions for improvement. You can use it as-is or review the recommendations
            in the Compliance Guidelines section below.
          </Text>
        </div>
      ) : null}

      {/* Footer with actions */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
        }}
      >
        <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
          {requiresModification ? (
            <Badge appearance="filled" color="danger" size="small" icon={<ErrorCircle20Regular />}>
              Requires Modification
            </Badge>
          ) : violations.length > 0 ? (
            <Badge appearance="filled" color="warning" size="small" icon={<Warning20Regular />}>
              Review Recommended
            </Badge>
          ) : (
            <Badge
              appearance="filled"
              color="success"
              size="small"
              icon={<CheckmarkCircle20Regular />}
            >
              Approved
            </Badge>
          )}
        </div>

        <div style={{ display: 'flex', gap: '4px', alignItems: 'center' }}>
          <Tooltip content={copied ? 'Copied!' : 'Copy text'} relationship="label">
            <Button
              appearance="subtle"
              icon={<Copy20Regular />}
              size="small"
              onClick={onCopyText}
              style={{ minWidth: '32px', color: tokens.colorNeutralForeground3 }}
            />
          </Tooltip>
          <Tooltip content="Regenerate" relationship="label">
            <Button
              appearance="subtle"
              icon={<ArrowSync20Regular />}
              size="small"
              onClick={onRegenerate}
              disabled={isLoading}
              style={{ minWidth: '32px', color: tokens.colorNeutralForeground3 }}
            />
          </Tooltip>
        </div>
      </div>

      {/* AI disclaimer */}
      <Text
        size={100}
        style={{
          color: tokens.colorNeutralForeground4,
          display: 'block',
          marginTop: '8px',
        }}
      >
        {AI_DISCLAIMER}
      </Text>

      {/* Collapsible Compliance Accordion */}
      {violations.length > 0 && (
        <Accordion
          collapsible
          style={{
            marginTop: '16px',
            borderTop: `1px solid ${tokens.colorNeutralStroke2}`,
            paddingTop: '8px',
          }}
        >
          <AccordionItem value="compliance">
            <AccordionHeader expandIconPosition="end" style={{ padding: '8px 0' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                {requiresModification ? (
                  <ErrorCircle20Regular style={{ color: '#d13438' }} />
                ) : violations.some((v) => v.severity === 'error') ? (
                  <ErrorCircle20Regular style={{ color: '#d13438' }} />
                ) : violations.some((v) => v.severity === 'warning') ? (
                  <Warning20Regular style={{ color: '#ffb900' }} />
                ) : (
                  <Info20Regular style={{ color: '#0078d4' }} />
                )}
                <Text weight="semibold" size={200}>
                  Compliance Guidelines ({violations.length}{' '}
                  {violations.length === 1 ? 'item' : 'items'})
                </Text>
              </div>
            </AccordionHeader>
            <AccordionPanel>
              <div style={{ paddingTop: '8px' }}>
                {violations.map((violation, index) => (
                  <ViolationCard key={index} violation={violation} />
                ))}
              </div>
            </AccordionPanel>
          </AccordionItem>
        </Accordion>
      )}
    </>
  );
});
ComplianceSection.displayName = 'ComplianceSection';
