import { runPromptPipeline } from "@/lib/ai";
import type { BrandPromptContext, PromptBuildContext, PromptUseCase, RagPromptDocument } from "@/lib/ai";
import type { BrandProfile, GenerateRequest, GenerateResponse, MarketingContentType } from "@/lib/types";
import type { LegacyGenerationClient } from "./types";

function mapUseCase(contentType: GenerateRequest["contentType"]): PromptUseCase | null {
  if (contentType === "social" || contentType === "social_post") return "social_post";
  if (contentType === "newsletter" || contentType === "email") return "email";
  if (contentType === "ad" || contentType === "ad_copy") return "ad";
  return null;
}

function normalizeMarketingContentType(contentType: GenerateRequest["contentType"]): MarketingContentType {
  if (contentType === "social_post") return "social";
  if (contentType === "newsletter") return "email";
  if (contentType === "ad_copy") return "ad";
  return contentType as MarketingContentType;
}

function toBrandPromptContext(profile: BrandProfile | null): BrandPromptContext | undefined {
  if (!profile) return undefined;
  return {
    name: profile.name,
    positioning: profile.positioning,
    voice: profile.voice,
    toneGuidelines: profile.tone_guidelines,
    audienceSummary: profile.audience_summary,
    approvedTerms: profile.approved_terms,
    bannedTerms: profile.banned_terms,
    complianceNotes: profile.compliance_notes,
    brandValues: profile.brand_values,
  };
}

function toRagDocuments(matches: Awaited<ReturnType<LegacyGenerationClient["searchKnowledge"]>>): RagPromptDocument[] {
  return matches.map((match) => ({
    id: match.chunk_id,
    title: match.title,
    content: match.content,
    similarity: match.similarity,
    sourceKind: match.source_kind,
    contentType: match.content_type ?? undefined,
    language: match.language,
    channel: match.channel,
    tags: match.tags,
  }));
}

function buildPromptContext(
  request: GenerateRequest,
  useCase: PromptUseCase,
  brand: BrandPromptContext | undefined,
  ragDocuments: RagPromptDocument[],
): PromptBuildContext {
  return {
    useCase,
    variantId: request.variantId,
    brand,
    ragDocuments,
    userInput: {
      topic: request.topic,
      brief: request.previousContent
        ? `Revise the previous draft using this feedback: ${request.feedback ?? ""}`
        : request.topic,
      audience: request.audience,
      language: request.language,
      tone: request.tone,
      contentType: normalizeMarketingContentType(request.contentType),
      channel: useCase === "social_post" ? "linkedin" : useCase === "email" ? "email" : "ads",
      sourceText: request.previousContent,
      constraints: [
        `Target length: ${request.length}`,
        `Knowledge source preference: ${request.knowledgeBase}`,
      ],
    },
  };
}

function generationMetadata(
  request: GenerateRequest,
  content: string,
  result: Awaited<ReturnType<typeof runPromptPipeline>>,
  brandProfileUsed: boolean,
  ragContextUsed: boolean,
): GenerateResponse["metadata"] {
  const evaluation = result.evaluation;
  return {
    topic: request.topic,
    contentType: request.contentType,
    language: request.language,
    tone: request.tone,
    length: request.length,
    knowledgeBase: request.knowledgeBase,
    wordCount: content.split(/\s+/).filter(Boolean).length,
    generatedAt: new Date().toISOString(),
    generationId: crypto.randomUUID(),
    framework: "ts-prompt-framework",
    promptRunId: result.runId,
    templateId: result.finalPrompt.templateId,
    templateVersion: result.finalPrompt.templateVersion,
    variantId: result.selectedVariantId,
    uniquenessScore: evaluation?.score,
    baselineSimilarity: evaluation?.cosineSimilarity,
    lexicalDiversity: evaluation?.lexicalDiversity,
    sentenceVariation: evaluation?.sentenceVariation,
    ragContextUsed,
    brandProfileUsed,
  };
}

export class TsPromptGenerationService {
  constructor(private readonly client: LegacyGenerationClient) {}

  supports(request: GenerateRequest): boolean {
    return mapUseCase(request.contentType) !== null;
  }

  async generate(request: GenerateRequest, options: { abTestVariants?: boolean } = {}): Promise<GenerateResponse> {
    const useCase = mapUseCase(request.contentType);
    if (!useCase) throw new Error(`Unsupported TypeScript prompt framework content type: ${request.contentType}`);

    const [brandProfile, knowledgeMatches] = await Promise.all([
      request.clientId
        ? this.client.getBrandProfile({ clientId: request.clientId, projectId: request.projectId }).catch(() => null)
        : Promise.resolve(null),
      request.clientId
        ? this.client.searchKnowledge({
            query: request.topic,
            clientId: request.clientId,
            projectId: request.projectId,
            contentType: normalizeMarketingContentType(request.contentType),
            language: request.language,
          }).catch(() => [])
        : Promise.resolve([]),
    ]);

    const ragDocuments = toRagDocuments(knowledgeMatches);
    const promptContext = buildPromptContext(request, useCase, toBrandPromptContext(brandProfile), ragDocuments);
    const variants = request.variantId
      ? [request.variantId]
      : options.abTestVariants
        ? ["precision-v1", "opinionated-v1", "evidence-led-v1"]
        : ["precision-v1"];

    const pipeline = await runPromptPipeline(
      promptContext,
      {
        generate: (input) => this.client.generateText(input),
      },
      {
        variantIds: variants,
        includeBaseline: true,
        autoSelectBestVariant: options.abTestVariants ?? false,
      },
    );

    const response: GenerateResponse = {
      content: pipeline.finalOutput,
      sources: ragDocuments.map((doc) => ({
        filename: doc.title,
        words: doc.content.split(/\s+/).filter(Boolean).length,
        source: doc.sourceKind === "competitor" || doc.sourceKind === "market" ? "secondary" : "primary",
      })),
      metadata: generationMetadata(request, pipeline.finalOutput, pipeline, Boolean(brandProfile), ragDocuments.length > 0),
    };

    await this.client.saveGeneratedOutput({
      request,
      response,
      prompt: pipeline.finalPrompt.observability.promptText,
      retrievedChunkIds: pipeline.finalPrompt.contextSummary.ragDocumentIds,
    });

    return response;
  }
}
