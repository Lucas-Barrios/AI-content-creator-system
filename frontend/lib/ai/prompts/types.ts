import type { CampaignChannel, Language, MarketingChannel, MarketingContentType, RepurposeFormat } from "@/lib/types";

export type PromptUseCase = "campaign" | "social_post" | "email" | "ad" | "repurpose";
export type PromptSectionKind =
  | "system"
  | "context"
  | "task"
  | "strategy"
  | "style"
  | "distinctiveness"
  | "output_format"
  | "quality_bar";

export interface PromptSection {
  kind: PromptSectionKind;
  title: string;
  content: string;
  optional?: boolean;
}

export interface PromptTemplate {
  id: string;
  version: string;
  useCase: PromptUseCase;
  label: string;
  description: string;
  sections: PromptSection[];
  outputMode: "text" | "json" | "structured_text";
  metadata?: Record<string, string | number | boolean>;
}

export interface PromptVariant {
  id: string;
  templateId: string;
  version: string;
  label: string;
  weight: number;
  sectionOverrides?: Partial<Record<PromptSectionKind, string>>;
  minimumUniquenessScore?: number;
}

export interface BrandPromptContext {
  name?: string;
  positioning?: string;
  voice?: string;
  toneGuidelines?: string;
  audienceSummary?: string;
  approvedTerms?: string[];
  bannedTerms?: string[];
  complianceNotes?: string;
  brandValues?: string[];
}

export interface RagPromptDocument {
  id: string;
  title: string;
  content: string;
  similarity?: number;
  sourceKind?: string;
  contentType?: MarketingContentType;
  language?: string | null;
  channel?: MarketingChannel | null;
  tags?: string[];
}

export interface CampaignPromptContext {
  goal?: string;
  offer?: string;
  audience?: string;
  channels?: CampaignChannel[];
  startDate?: string;
  endDate?: string;
  coreMessage?: string;
  conceptSummary?: string;
  ctaSuggestions?: string[];
}

export interface UserPromptInput {
  topic?: string;
  brief?: string;
  audience?: string;
  language: Language | string;
  tone?: string;
  contentType?: MarketingContentType;
  channel?: MarketingChannel | CampaignChannel | RepurposeFormat;
  sourceText?: string;
  sourceFormat?: string;
  targetFormat?: string;
  constraints?: string[];
}

export interface PromptBuildContext {
  useCase: PromptUseCase;
  userInput: UserPromptInput;
  brand?: BrandPromptContext;
  campaign?: CampaignPromptContext;
  ragDocuments?: RagPromptDocument[];
  variantId?: string;
  runId?: string;
}

export interface AssembledPrompt {
  templateId: string;
  templateVersion: string;
  variantId: string;
  useCase: PromptUseCase;
  system: string;
  user: string;
  sections: PromptSection[];
  contextSummary: {
    brandIncluded: boolean;
    campaignIncluded: boolean;
    ragDocumentIds: string[];
  };
  observability: PromptObservabilityRecord;
}

export interface PromptObservabilityRecord {
  runId: string;
  templateId: string;
  templateVersion: string;
  variantId: string;
  useCase: PromptUseCase;
  promptText: string;
  retrievedContext: RagPromptDocument[];
  brandSnapshot?: BrandPromptContext;
  campaignSnapshot?: CampaignPromptContext;
  createdAt: string;
}

export interface PipelineStepResult {
  step: "strategy" | "angle_selection" | "generation" | "refinement" | "evaluation";
  prompt: AssembledPrompt;
  response: string;
  metadata?: Record<string, unknown>;
}

export interface PromptPipelineResult {
  runId: string;
  selectedVariantId: string;
  finalPrompt: AssembledPrompt;
  finalOutput: string;
  baselineOutput?: string;
  steps: PipelineStepResult[];
  evaluation?: UniquenessReport;
}

export interface UniquenessReport {
  score: number;
  cosineSimilarity: number;
  lexicalDiversity: number;
  baselineLexicalDiversity: number;
  sentenceVariation: number;
  baselineSentenceVariation: number;
  distinctTermRatio: number;
  genericPhraseCount: number;
  baselineGenericPhraseCount: number;
  recommendation: "use" | "refine" | "reject";
  notes: string[];
}

export interface PromptEvaluationCandidate {
  variant: PromptVariant;
  output: string;
  baselineOutput: string;
}
