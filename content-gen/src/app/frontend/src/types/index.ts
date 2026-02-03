/**
 * Type definitions for the Content Generation Solution Accelerator
 */

export interface CreativeBrief {
  overview: string;
  objectives: string;
  target_audience: string;
  key_message: string;
  tone_and_style: string;
  deliverable: string;
  timelines: string;
  visual_guidelines: string;
  cta: string;
}

export interface Product {
  product_name: string;
  description: string;
  tags: string;
  price: number;
  sku: string;
  image_url?: string;
  hex_value?: string; // Color hex code for paint products
  // Legacy fields for backward compatibility
  category?: string;
  sub_category?: string;
  marketing_description?: string;
  detailed_spec_description?: string;
  model?: string;
  image_description?: string;
}

export interface ComplianceViolation {
  severity: 'error' | 'warning' | 'info';
  message: string;
  suggestion: string;
  field: string;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  agent?: string;
  timestamp: string;
  violations?: ComplianceViolation[];
}

export interface Conversation {
  id: string;
  user_id: string;
  messages: ChatMessage[];
  brief?: CreativeBrief;
  updated_at: string;
}

export interface AgentResponse {
  type: 'agent_response' | 'error' | 'status' | 'heartbeat';
  agent?: string;
  content: string;
  is_final: boolean;
  requires_user_input?: boolean;
  request_id?: string;
  conversation_history?: string;
  count?: number;
  elapsed?: number;
  message?: string;
  metadata?: {
    conversation_id?: string;
    handoff_to?: string;
  };
}

export interface BrandGuidelines {
  tone: string;
  voice: string;
  primary_color: string;
  secondary_color: string;
  prohibited_words: string[];
  required_disclosures: string[];
  max_headline_length: number;
  max_body_length: number;
  require_cta: boolean;
}

export interface ParsedBriefResponse {
  brief?: CreativeBrief;
  requires_confirmation: boolean;
  requires_clarification?: boolean;
  clarifying_questions?: string;
  rai_blocked?: boolean;
  message: string;
  conversation_id?: string;
}

export interface GeneratedContent {
  text_content?: {
    headline?: string;
    body?: string;
    cta_text?: string;
    tagline?: string;
  };
  image_content?: {
    image_base64?: string;
    image_url?: string;
    alt_text?: string;
    prompt_used?: string;
  };
  violations: ComplianceViolation[];
  requires_modification: boolean;
  // Error fields for when generation fails
  error?: string;
  image_error?: string;
  text_error?: string;
}

export interface AppConfig {
  app_name: string;
  show_brand_guidelines: boolean;
  enable_image_generation: boolean;
  image_model?: string;
  enable_compliance_check: boolean;
  max_file_size_mb: number;
}
