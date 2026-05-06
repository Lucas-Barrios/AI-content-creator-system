export type ContentType = "blog" | "social" | "program" | "newsletter" | "email" | "ad" | "ad_copy" | "social_post";
export type Language = "english" | "german";
export type KnowledgeBaseSource = "hybrid" | "primary" | "secondary";
export type Length = "Short" | "Medium" | "Long";
export type KnowledgeSourceKind = "brand" | "product" | "audience" | "market" | "competitor" | "campaign" | "policy" | "other";
export type MarketingContentType = ContentType | "email" | "ad" | "landing_page" | "other";
export type MarketingChannel = "website" | "linkedin" | "instagram" | "facebook" | "x" | "email" | "newsletter" | "ads" | "blog" | "other";

export interface SourceFile {
  filename: string;
  words: number;
  source: "primary" | "secondary";
}

export interface GenerateRequest {
  organizationId?: string;
  clientId?: string;
  projectId?: string;
  brandProfileId?: string;
  contentType: ContentType;
  topic: string;
  audience: string;
  language: Language;
  tone: string;
  length: Length;
  knowledgeBase: KnowledgeBaseSource;
  files?: UploadedFile[];
  feedback?: string;
  previousContent?: string;
  compareWithLegacy?: boolean;
  variantId?: "precision-v1" | "opinionated-v1" | "evidence-led-v1";
}

export interface UploadedFile {
  id: string;
  name: string;
  size: number;
  contentType: string;
  url?: string;
}

export interface GenerateResponse {
  content: string;
  sources: SourceFile[];
  metadata: {
    topic: string;
    contentType: ContentType;
    language: Language;
    tone: string;
    length: Length;
    knowledgeBase: KnowledgeBaseSource;
      wordCount: number;
      generatedAt: string;
      generationId: string;
      framework?: "legacy-python" | "ts-prompt-framework";
      fallbackReason?: string;
      promptRunId?: string;
      templateId?: string;
      templateVersion?: string;
      variantId?: string;
      uniquenessScore?: number;
      baselineSimilarity?: number;
      lexicalDiversity?: number;
      sentenceVariation?: number;
      ragContextUsed?: boolean;
      brandProfileUsed?: boolean;
      comparison?: {
        newFrameworkUniquenessScore: number;
        legacyUniquenessScore: number;
        baselineSimilarity: number;
        recommendedWinner: "new_framework" | "legacy";
      };
  };
  legacyOutput?: string;
  newFrameworkOutput?: string;
  selectedOutput?: string;
}

export type FeedbackStatus = "approved" | "needs_revision";

export interface FeedbackRequest {
  generationId: string;
  status: FeedbackStatus;
  comment: string;
  request: GenerateRequest;
  response: GenerateResponse;
}

export interface FeedbackResponse {
  id: string;
  generationId: string;
  status: FeedbackStatus;
  createdAt: string;
}

export interface WorkspaceSelection {
  organizationId: string;
  clientId: string;
  projectId: string;
  clientName: string;
  projectName: string;
}

export interface HealthResponse {
  status: string;
}

export interface KnowledgeTextRequest {
  organizationId: string;
  clientId: string;
  projectId?: string;
  title: string;
  text: string;
  sourceKind: KnowledgeSourceKind;
  contentType?: MarketingContentType;
  language?: Language;
  channel?: MarketingChannel;
  tags?: string[];
  metadata?: Record<string, unknown>;
}

export interface KnowledgeIngestionResponse {
  documentId: string;
  duplicate: boolean;
  contentHash: string;
  chunkCount: number;
  embeddingCount: number;
  status: string;
  message: string;
}

export interface KnowledgeSearchRequest {
  query: string;
  clientId?: string;
  projectId?: string;
  contentType?: MarketingContentType;
  language?: Language;
  channel?: MarketingChannel;
  matchCount?: number;
  matchThreshold?: number;
}

export interface KnowledgeMatch {
  chunk_id: string;
  document_id: string;
  client_id: string;
  project_id: string | null;
  title: string;
  content: string;
  source_kind: KnowledgeSourceKind;
  content_type: MarketingContentType | null;
  language: string | null;
  channel: MarketingChannel | null;
  tags: string[];
  similarity: number;
}

export interface KnowledgeSearchResponse {
  matches: KnowledgeMatch[];
  count: number;
}

export interface BrandProfile {
  id?: string;
  organization_id?: string;
  client_id?: string;
  project_id?: string | null;
  name: string;
  positioning: string;
  voice: string;
  tone_guidelines: string;
  audience_summary: string;
  approved_terms: string[];
  banned_terms: string[];
  compliance_notes: string;
  brand_values: string[];
}

export interface BrandProfileRequest {
  organizationId: string;
  clientId: string;
  projectId?: string;
  name: string;
  positioning: string;
  voice: string;
  toneGuidelines: string;
  audienceSummary: string;
  approvedTerms: string[];
  bannedTerms: string[];
  complianceNotes: string;
  brandValues: string[];
}

export interface GeneratedOutputRecord {
  id: string;
  title: string | null;
  content: string;
  content_type: string;
  channel: string | null;
  language: string;
  status: string;
  created_at: string;
}

// ── Campaign Generator ──────────────────────────────────────────────────────

export type CampaignChannel = "linkedin" | "instagram" | "email" | "blog" | "ads";
export type CampaignTone = "Academic" | "Formal" | "Professional" | "Friendly" | "Conversational";

export interface ContentIdea {
  id: number;
  title: string;
  channel: string;
  format: string;
  hook: string;
  week: number;
}

export interface CalendarEntry {
  week: number;
  day: string;
  channel: string;
  title: string;
  content_type: string;
}

export interface CampaignConcept {
  name: string;
  conceptSummary: string;
  coreMessage: string;
  audienceAngle: string;
  channelStrategy: string;
  contentIdeas: ContentIdea[];
  ctaSuggestions: string[];
  calendarDraft: CalendarEntry[];
}

export interface CampaignAsset {
  assetId: string;
  campaignItemId: string;
  channel: CampaignChannel;
  label: string;
  contentType: string;
  content: string;
  status: "draft" | "approved" | "needs_revision";
}

export interface CampaignRequest {
  organizationId: string;
  clientId: string;
  projectId: string;
  goal: string;
  offer: string;
  audience: string;
  channels: CampaignChannel[];
  startDate: string;
  endDate: string;
  language: Language;
  tone: string;
  kbSource: KnowledgeBaseSource;
  brandProfileId?: string;
  extraContext?: string;
}

export interface CampaignResult {
  campaignId: string;
  createdAt: string;
  concept: CampaignConcept;
  assets: CampaignAsset[];
}

export interface CampaignSummary {
  id: string;
  name: string;
  objective: string;
  audience: string;
  channels: string[];
  status: string;
  start_date: string;
  end_date: string;
  created_at: string;
}

// ── Content Repurposing Engine ──────────────────────────────────────────────

export type RepurposeFormat =
  | "linkedin"
  | "instagram"
  | "email"
  | "blog_summary"
  | "ad_copy"
  | "landing_page"
  | "video_script";

export type SourceType =
  | "blog_post"
  | "transcript"
  | "webinar_notes"
  | "article"
  | "social_post"
  | "document"
  | "other";

export interface ContentExtraction {
  title: string;
  coreArgument: string;
  keyPoints: string[];
  facts: string[];
  quotes: string[];
  tone: string;
  audienceSignals: string;
  oneSentenceSummary: string;
  raw: Record<string, unknown>;
}

export interface RepurposedOutput {
  outputId: string;
  format: RepurposeFormat;
  label: string;
  contentType: string;
  channel: string;
  content: string;
  wordCount: number;
  status: "draft" | "approved" | "needs_revision";
}

export interface RepurposeRequest {
  organizationId: string;
  clientId: string;
  projectId: string;
  sourceText: string;
  sourceTitle: string;
  sourceType: SourceType;
  targetFormats: RepurposeFormat[];
  language: Language;
  preserveTone: boolean;
  brandProfileId?: string;
}

export interface RepurposeResult {
  sourceId: string;
  createdAt: string;
  extraction: ContentExtraction;
  outputs: RepurposedOutput[];
}

export interface RepurposeOutputRegenerateRequest {
  format: RepurposeFormat;
  extractionRaw: Record<string, unknown>;
  language: Language;
  brandProfileId?: string;
}

export interface AssetRegenerateRequest {
  channel: CampaignChannel;
  conceptRaw: Record<string, unknown>;
  language: Language;
  brandProfileId?: string;
  extraContext?: string;
}

export interface ApiErrorBody {
  error: string;
  detail?: string;
  status?: number;
}

export interface HistoryItem {
  id: string;
  request: GenerateRequest;
  response: GenerateResponse;
}
