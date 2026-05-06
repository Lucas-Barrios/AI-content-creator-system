import { DISTINCTIVENESS_BLOCK, QUALITY_BAR_BLOCK } from "./constraints";
import type { PromptTemplate, PromptUseCase, PromptVariant } from "./types";

const BASE_SYSTEM = `You are a senior marketing strategist and copy lead for an AI marketing content operating system.
You create precise, brand-consistent marketing assets for SMEs.
You must use supplied brand, campaign, and retrieval context before relying on general knowledge.`;

const STRATEGY_STEP = `Before drafting, create a compact internal strategy:
1. Audience decision state
2. Main friction or motivation
3. Specific message angle
4. Proof/context to use
5. Channel-specific structure
Use the strategy to write the final answer, but do not expose hidden notes unless the output format requests them.`;

export const PROMPT_TEMPLATES: PromptTemplate[] = [
  {
    id: "campaign-master",
    version: "1.0.0",
    useCase: "campaign",
    label: "Campaign Strategy Generator",
    description: "Builds differentiated multi-channel campaign concepts and asset directions.",
    outputMode: "json",
    sections: [
      { kind: "system", title: "System", content: BASE_SYSTEM },
      { kind: "context", title: "Context", content: "{{context_block}}" },
      { kind: "task", title: "Task", content: "Generate a complete campaign strategy for the supplied goal, offer, audience, channels, and dates." },
      { kind: "strategy", title: "Strategy", content: STRATEGY_STEP },
      { kind: "distinctiveness", title: "Distinctiveness", content: DISTINCTIVENESS_BLOCK },
      {
        kind: "output_format",
        title: "Output Format",
        content:
          'Return valid JSON with keys: "name", "conceptSummary", "coreMessage", "audienceAngle", "channelStrategy", "contentIdeas", "ctaSuggestions", "calendarDraft".',
      },
      { kind: "quality_bar", title: "Quality Bar", content: QUALITY_BAR_BLOCK },
    ],
  },
  {
    id: "social-post",
    version: "1.0.0",
    useCase: "social_post",
    label: "Social Post Generator",
    description: "Creates channel-native LinkedIn, Instagram, Facebook, or X posts.",
    outputMode: "structured_text",
    sections: [
      { kind: "system", title: "System", content: BASE_SYSTEM },
      { kind: "context", title: "Context", content: "{{context_block}}" },
      { kind: "task", title: "Task", content: "Write one social post for the requested channel and audience." },
      { kind: "strategy", title: "Strategy", content: STRATEGY_STEP },
      { kind: "distinctiveness", title: "Distinctiveness", content: DISTINCTIVENESS_BLOCK },
      {
        kind: "output_format",
        title: "Output Format",
        content:
          "Return plain text only. Use a strong first line, 2-4 compact body paragraphs, one clear CTA, and platform-appropriate hashtags only when useful.",
      },
      { kind: "quality_bar", title: "Quality Bar", content: QUALITY_BAR_BLOCK },
    ],
  },
  {
    id: "email",
    version: "1.0.0",
    useCase: "email",
    label: "Email Generator",
    description: "Creates concise campaign or newsletter email copy.",
    outputMode: "structured_text",
    sections: [
      { kind: "system", title: "System", content: BASE_SYSTEM },
      { kind: "context", title: "Context", content: "{{context_block}}" },
      { kind: "task", title: "Task", content: "Write a complete marketing email for the supplied audience and offer." },
      { kind: "strategy", title: "Strategy", content: STRATEGY_STEP },
      { kind: "distinctiveness", title: "Distinctiveness", content: DISTINCTIVENESS_BLOCK },
      {
        kind: "output_format",
        title: "Output Format",
        content:
          "Use exact labels: SUBJECT, PREVIEW, BODY, CTA. Subject max 9 words. Preview max 12 words. Body should be skimmable and specific.",
      },
      { kind: "quality_bar", title: "Quality Bar", content: QUALITY_BAR_BLOCK },
    ],
  },
  {
    id: "ad-copy",
    version: "1.0.0",
    useCase: "ad",
    label: "Ad Copy Generator",
    description: "Creates paid search, paid social, and retargeting copy variants.",
    outputMode: "structured_text",
    sections: [
      { kind: "system", title: "System", content: BASE_SYSTEM },
      { kind: "context", title: "Context", content: "{{context_block}}" },
      { kind: "task", title: "Task", content: "Create ad copy variants for the supplied offer, audience, and channel." },
      { kind: "strategy", title: "Strategy", content: STRATEGY_STEP },
      { kind: "distinctiveness", title: "Distinctiveness", content: DISTINCTIVENESS_BLOCK },
      {
        kind: "output_format",
        title: "Output Format",
        content:
          "Return three variants: Search Ad, Social Ad, Retargeting. Respect common ad-length constraints and lead with concrete outcomes.",
      },
      { kind: "quality_bar", title: "Quality Bar", content: QUALITY_BAR_BLOCK },
    ],
  },
  {
    id: "repurpose",
    version: "1.0.0",
    useCase: "repurpose",
    label: "Content Repurposer",
    description: "Transforms existing source copy into a new channel while preserving meaning.",
    outputMode: "structured_text",
    sections: [
      { kind: "system", title: "System", content: BASE_SYSTEM },
      { kind: "context", title: "Context", content: "{{context_block}}" },
      { kind: "task", title: "Task", content: "Repurpose the source content into the requested target format without adding unsupported facts." },
      {
        kind: "strategy",
        title: "Strategy",
        content:
          "Extract the source thesis, audience, facts, proof points, and CTA. Then adapt structure and emphasis for the target format.",
      },
      { kind: "distinctiveness", title: "Distinctiveness", content: DISTINCTIVENESS_BLOCK },
      { kind: "output_format", title: "Output Format", content: "Return only the final repurposed asset in the requested format." },
      { kind: "quality_bar", title: "Quality Bar", content: QUALITY_BAR_BLOCK },
    ],
  },
];

export const PROMPT_VARIANTS: PromptVariant[] = [
  {
    id: "precision-v1",
    templateId: "*",
    version: "1.0.0",
    label: "Precision",
    weight: 1,
    minimumUniquenessScore: 72,
    sectionOverrides: {
      style: "Style: clear, specific, restrained, and commercially useful. Avoid hype.",
    },
  },
  {
    id: "opinionated-v1",
    templateId: "*",
    version: "1.0.0",
    label: "Opinionated",
    weight: 1,
    minimumUniquenessScore: 78,
    sectionOverrides: {
      distinctiveness:
        `${DISTINCTIVENESS_BLOCK}\n- Add one defensible point of view that a generic competitor would be unlikely to say.`,
    },
  },
  {
    id: "evidence-led-v1",
    templateId: "*",
    version: "1.0.0",
    label: "Evidence Led",
    weight: 1,
    minimumUniquenessScore: 76,
    sectionOverrides: {
      strategy:
        "Prioritise proof before persuasion: identify the strongest retrieved fact, the audience implication, and the CTA that follows from it.",
    },
  },
];

export function getTemplate(useCase: PromptUseCase, templateId?: string): PromptTemplate {
  const template = PROMPT_TEMPLATES.find((item) => item.useCase === useCase && (!templateId || item.id === templateId));
  if (!template) {
    throw new Error(`No prompt template found for use case '${useCase}'.`);
  }
  return template;
}

export function getVariant(variantId?: string): PromptVariant {
  const variant = variantId
    ? PROMPT_VARIANTS.find((item) => item.id === variantId)
    : PROMPT_VARIANTS[0];
  if (!variant) {
    throw new Error(`No prompt variant found for '${variantId}'.`);
  }
  return variant;
}
