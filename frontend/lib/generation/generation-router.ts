import { evaluateUniqueness } from "@/lib/ai";
import type { GenerateRequest, GenerateResponse } from "@/lib/types";
import { PythonGenerationClient } from "./python-generation-client";
import { TsPromptGenerationService } from "./ts-prompt-generation-service";
import type { GenerationRouterConfig, LegacyGenerationClient } from "./types";

export function readGenerationRouterConfig(): GenerationRouterConfig {
  return {
    enableTsPromptFramework: process.env.ENABLE_TS_PROMPT_FRAMEWORK === "true",
    mode: (process.env.TS_PROMPT_FRAMEWORK_MODE as GenerationRouterConfig["mode"]) || "social_only",
    abTestVariants: process.env.TS_PROMPT_AB_TEST === "true",
  };
}

function isModeSupported(request: GenerateRequest, service: TsPromptGenerationService, mode: GenerationRouterConfig["mode"]): boolean {
  if (!service.supports(request)) return false;
  if (mode === "all" || mode === "supported") return true;
  return request.contentType === "social" || request.contentType === "social_post";
}

function withLegacyMetadata(response: GenerateResponse, fallbackReason?: string): GenerateResponse {
  return {
    ...response,
    metadata: {
      ...response.metadata,
      framework: "legacy-python",
      fallbackReason,
      generatedAt: response.metadata.generatedAt || new Date().toISOString(),
    },
  };
}

function recommendedWinner(newFramework: GenerateResponse, legacy: GenerateResponse): "new_framework" | "legacy" {
  const newScore = newFramework.metadata.uniquenessScore ?? 0;
  const legacyScore = legacy.metadata.uniquenessScore ?? 0;
  return newScore >= legacyScore ? "new_framework" : "legacy";
}

export class GenerationRouter {
  private readonly tsService: TsPromptGenerationService;

  constructor(
    private readonly client: LegacyGenerationClient = new PythonGenerationClient(),
    private readonly config: GenerationRouterConfig = readGenerationRouterConfig(),
  ) {
    this.tsService = new TsPromptGenerationService(client);
  }

  async generate(request: GenerateRequest): Promise<GenerateResponse> {
    if (request.compareWithLegacy) return this.compare(request);

    if (!this.config.enableTsPromptFramework || !isModeSupported(request, this.tsService, this.config.mode)) {
      const legacy = withLegacyMetadata(await this.client.generate(request));
      await this.client.saveGeneratedOutput({ request, response: legacy });
      return legacy;
    }

    try {
      return await this.tsService.generate(request, { abTestVariants: this.config.abTestVariants });
    } catch (error) {
      console.error("TS prompt framework failed; falling back to legacy Python generation:", error);
      const legacy = withLegacyMetadata(await this.client.generate(request), "ts_prompt_framework_failed");
      await this.client.saveGeneratedOutput({ request, response: legacy });
      return legacy;
    }
  }

  async compare(request: GenerateRequest): Promise<GenerateResponse> {
    const legacy = withLegacyMetadata(await this.client.generate({ ...request, compareWithLegacy: false }));
    let newFramework: GenerateResponse | null = null;

    if (this.config.enableTsPromptFramework && isModeSupported(request, this.tsService, this.config.mode)) {
      try {
        newFramework = await this.tsService.generate({ ...request, compareWithLegacy: false }, { abTestVariants: this.config.abTestVariants });
      } catch (error) {
        console.error("TS prompt framework comparison branch failed:", error);
      }
    }

    if (!newFramework) {
      await this.client.saveGeneratedOutput({ request, response: legacy });
      return {
        ...legacy,
        selectedOutput: legacy.content,
        legacyOutput: legacy.content,
        metadata: {
          ...legacy.metadata,
          fallbackReason: "ts_prompt_framework_unavailable_for_comparison",
        },
      };
    }

    const baseline = `Write ${request.contentType} marketing content about ${request.topic} for ${request.audience}.`;
    const legacyReport = evaluateUniqueness(legacy.content, baseline);
    const newReport = evaluateUniqueness(newFramework.content, baseline);
    const winner = recommendedWinner(
      { ...newFramework, metadata: { ...newFramework.metadata, uniquenessScore: newReport.score } },
      { ...legacy, metadata: { ...legacy.metadata, uniquenessScore: legacyReport.score } },
    );
    const selected = winner === "new_framework" ? newFramework : legacy;

    const response: GenerateResponse = {
      ...selected,
      content: selected.content,
      selectedOutput: selected.content,
      legacyOutput: legacy.content,
      newFrameworkOutput: newFramework.content,
      metadata: {
        ...selected.metadata,
        comparison: {
          newFrameworkUniquenessScore: newReport.score,
          legacyUniquenessScore: legacyReport.score,
          baselineSimilarity: newReport.cosineSimilarity,
          recommendedWinner: winner,
        },
      },
    };

    await this.client.saveGeneratedOutput({ request, response });
    return response;
  }
}
