import { evaluateUniqueness, selectBestVariant } from "../evaluation/uniqueness";
import { buildGenericBaselinePrompt, buildPrompt } from "../prompt-builder/prompt-builder";
import { PROMPT_VARIANTS } from "../prompts/templates";
import type {
  AssembledPrompt,
  PipelineStepResult,
  PromptBuildContext,
  PromptPipelineResult,
  PromptVariant,
} from "../prompts/types";

export interface PromptModelClient {
  generate(input: {
    system?: string;
    prompt: string;
    temperature?: number;
    metadata?: Record<string, unknown>;
  }): Promise<string>;
}

export interface PipelineOptions {
  variantIds?: string[];
  temperature?: number;
  includeBaseline?: boolean;
  autoSelectBestVariant?: boolean;
}

async function runStep(
  client: PromptModelClient,
  step: PipelineStepResult["step"],
  prompt: AssembledPrompt,
  temperature?: number,
  metadata?: Record<string, unknown>,
): Promise<PipelineStepResult> {
  const response = await client.generate({
    system: prompt.system,
    prompt: prompt.user,
    temperature,
    metadata: {
      ...metadata,
      promptRunId: prompt.observability.runId,
      templateId: prompt.templateId,
      templateVersion: prompt.templateVersion,
      variantId: prompt.variantId,
      step,
    },
  });

  return { step, prompt, response, metadata };
}

function getPipelineVariants(ids?: string[]): PromptVariant[] {
  if (!ids?.length) return PROMPT_VARIANTS;
  const selected = PROMPT_VARIANTS.filter((variant) => ids.includes(variant.id));
  if (selected.length === 0) {
    throw new Error(`No prompt variants found for: ${ids.join(", ")}`);
  }
  return selected;
}

export async function runPromptPipeline(
  context: PromptBuildContext,
  client: PromptModelClient,
  options: PipelineOptions = {},
): Promise<PromptPipelineResult> {
  const runId = context.runId ?? `pipeline_${Date.now()}_${Math.random().toString(36).slice(2, 10)}`;
  const variants = getPipelineVariants(options.variantIds);
  const baselinePrompt = buildGenericBaselinePrompt(context);
  const baselineOutput = options.includeBaseline !== false
    ? await client.generate({
        prompt: baselinePrompt,
        temperature: options.temperature,
        metadata: { runId, step: "baseline", useCase: context.useCase },
      })
    : "";

  const candidateOutputs = [];
  const candidateSteps: PipelineStepResult[][] = [];

  for (const variant of variants) {
    const variantContext = { ...context, runId, variantId: variant.id };
    const strategyPrompt = buildPrompt({
      ...variantContext,
      userInput: {
        ...variantContext.userInput,
        constraints: [...(variantContext.userInput.constraints ?? []), "Return only the strategy summary for this step."],
      },
    });
    const strategy = await runStep(client, "strategy", strategyPrompt, options.temperature);

    const anglePrompt = buildPrompt({
      ...variantContext,
      userInput: {
        ...variantContext.userInput,
        constraints: [
          ...(variantContext.userInput.constraints ?? []),
          `Use this strategy summary to choose the strongest angle: ${strategy.response}`,
          "Return only the selected angle and rationale.",
        ],
      },
    });
    const angle = await runStep(client, "angle_selection", anglePrompt, options.temperature);

    const generationPrompt = buildPrompt({
      ...variantContext,
      userInput: {
        ...variantContext.userInput,
        constraints: [
          ...(variantContext.userInput.constraints ?? []),
          `Selected angle: ${angle.response}`,
          "Generate the requested final asset now.",
        ],
      },
    });
    const generation = await runStep(client, "generation", generationPrompt, options.temperature);

    const refinementPrompt = buildPrompt({
      ...variantContext,
      userInput: {
        ...variantContext.userInput,
        constraints: [
          ...(variantContext.userInput.constraints ?? []),
          `Draft to refine: ${generation.response}`,
          "Improve specificity, remove generic phrasing, preserve facts, and return only the final version.",
        ],
      },
    });
    const refinement = await runStep(client, "refinement", refinementPrompt, options.temperature);

    candidateOutputs.push({ variant, output: refinement.response, baselineOutput });
    candidateSteps.push([strategy, angle, generation, refinement]);
  }

  const best = options.autoSelectBestVariant === false
    ? { variant: candidateOutputs[0].variant, report: evaluateUniqueness(candidateOutputs[0].output, baselineOutput) }
    : selectBestVariant(candidateOutputs);
  const bestIndex = candidateOutputs.findIndex((candidate) => candidate.variant.id === best.variant.id);
  const finalOutput = candidateOutputs[bestIndex].output;
  const finalPrompt = candidateSteps[bestIndex][candidateSteps[bestIndex].length - 1].prompt;
  const evaluationPrompt = buildPrompt({
    ...context,
    runId,
    variantId: best.variant.id,
    userInput: {
      ...context.userInput,
      constraints: [
        ...(context.userInput.constraints ?? []),
        `Uniqueness score: ${best.report.score}`,
        `Recommendation: ${best.report.recommendation}`,
      ],
    },
  });

  return {
    runId,
    selectedVariantId: best.variant.id,
    finalPrompt,
    finalOutput,
    baselineOutput,
    steps: [
      ...candidateSteps[bestIndex],
      {
        step: "evaluation",
        prompt: evaluationPrompt,
        response: JSON.stringify(best.report, null, 2),
        metadata: { selectedVariantId: best.variant.id },
      },
    ],
    evaluation: best.report,
  };
}
