import type { BrandProfile, GenerateRequest, GenerateResponse, KnowledgeMatch } from "@/lib/types";

export type GenerationFramework = "legacy-python" | "ts-prompt-framework";
export type GenerationWinner = "new_framework" | "legacy";

export interface GenerationRouterConfig {
  enableTsPromptFramework: boolean;
  mode: "social_only" | "supported" | "all";
  abTestVariants: boolean;
}

export interface LegacyGenerationClient {
  generate(payload: GenerateRequest): Promise<GenerateResponse>;
  generateText(input: { system?: string; prompt: string; metadata?: Record<string, unknown> }): Promise<string>;
  getBrandProfile(input: { clientId: string; projectId?: string }): Promise<BrandProfile | null>;
  searchKnowledge(input: {
    query: string;
    clientId: string;
    projectId?: string;
    contentType?: string;
    language?: string;
    channel?: string;
  }): Promise<KnowledgeMatch[]>;
  saveGeneratedOutput(input: {
    request: GenerateRequest;
    response: GenerateResponse;
    prompt?: string;
    retrievedChunkIds?: string[];
  }): Promise<void>;
}
