export type ContentType = "blog" | "social" | "program" | "newsletter";
export type Language = "english" | "german";
export type KnowledgeBaseSource = "hybrid" | "primary" | "secondary";
export type Length = "Short" | "Medium" | "Long";

export interface SourceFile {
  filename: string;
  words: number;
  source: "primary" | "secondary";
}

export interface GenerateRequest {
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
  };
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
