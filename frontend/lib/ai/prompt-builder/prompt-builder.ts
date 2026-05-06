import { getTemplate, getVariant } from "../prompts/templates";
import type { AssembledPrompt, PromptBuildContext, PromptSection } from "../prompts/types";

function compactList(values?: string[]): string {
  return values?.filter(Boolean).join(", ") || "Not specified";
}

function section(title: string, value?: string | null): string {
  const clean = value?.trim();
  return clean ? `${title}: ${clean}` : "";
}

function renderBrandBlock(context: PromptBuildContext): string {
  const brand = context.brand;
  if (!brand) return "";

  return [
    "BRAND PROFILE",
    section("Name", brand.name),
    section("Positioning", brand.positioning),
    section("Voice", brand.voice),
    section("Tone guidelines", brand.toneGuidelines),
    section("Audience summary", brand.audienceSummary),
    `Approved terms: ${compactList(brand.approvedTerms)}`,
    `Banned terms: ${compactList(brand.bannedTerms)}`,
    section("Compliance notes", brand.complianceNotes),
    `Brand values: ${compactList(brand.brandValues)}`,
  ]
    .filter(Boolean)
    .join("\n");
}

function renderCampaignBlock(context: PromptBuildContext): string {
  const campaign = context.campaign;
  if (!campaign) return "";

  return [
    "CAMPAIGN CONTEXT",
    section("Goal", campaign.goal),
    section("Offer", campaign.offer),
    section("Audience", campaign.audience),
    `Channels: ${compactList(campaign.channels)}`,
    section("Dates", campaign.startDate && campaign.endDate ? `${campaign.startDate} to ${campaign.endDate}` : undefined),
    section("Core message", campaign.coreMessage),
    section("Concept summary", campaign.conceptSummary),
    `CTA suggestions: ${compactList(campaign.ctaSuggestions)}`,
  ]
    .filter(Boolean)
    .join("\n");
}

function renderRagBlock(context: PromptBuildContext): string {
  const documents = context.ragDocuments?.slice(0, 8) ?? [];
  if (documents.length === 0) return "";

  const entries = documents.map((doc, index) => {
    const similarity = typeof doc.similarity === "number" ? ` | similarity ${doc.similarity.toFixed(3)}` : "";
    const metadata = [doc.sourceKind, doc.contentType, doc.language, doc.channel].filter(Boolean).join(" | ");
    return [
      `[${index + 1}] ${doc.title}${similarity}`,
      metadata ? `Metadata: ${metadata}` : "",
      doc.tags?.length ? `Tags: ${doc.tags.join(", ")}` : "",
      doc.content.trim(),
    ]
      .filter(Boolean)
      .join("\n");
  });

  return ["RETRIEVED KNOWLEDGE", ...entries].join("\n\n");
}

function renderUserInputBlock(context: PromptBuildContext): string {
  const input = context.userInput;
  return [
    "USER REQUEST",
    section("Topic", input.topic),
    section("Brief", input.brief),
    section("Audience", input.audience),
    section("Language", input.language),
    section("Tone", input.tone),
    section("Content type", input.contentType),
    section("Channel", input.channel),
    section("Source format", input.sourceFormat),
    section("Target format", input.targetFormat),
    input.constraints?.length ? `Additional constraints: ${input.constraints.join("; ")}` : "",
    input.sourceText ? `SOURCE TEXT\n${input.sourceText}` : "",
  ]
    .filter(Boolean)
    .join("\n");
}

export function buildContextBlock(context: PromptBuildContext): string {
  return [
    renderBrandBlock(context),
    renderCampaignBlock(context),
    renderRagBlock(context),
    renderUserInputBlock(context),
  ]
    .filter(Boolean)
    .join("\n\n---\n\n");
}

function applyVariantOverrides(sections: PromptSection[], contextBlock: string, variantId?: string): PromptSection[] {
  const variant = getVariant(variantId);
  return sections.map((promptSection) => {
    const override = variant.sectionOverrides?.[promptSection.kind];
    return {
      ...promptSection,
      content: (override ?? promptSection.content).replace("{{context_block}}", contextBlock),
    };
  });
}

export function buildPrompt(context: PromptBuildContext): AssembledPrompt {
  const template = getTemplate(context.useCase);
  const variant = getVariant(context.variantId);
  const contextBlock = buildContextBlock(context);
  const sections = applyVariantOverrides(template.sections, contextBlock, variant.id);
  const system = sections.find((item) => item.kind === "system")?.content ?? "";
  const user = sections
    .filter((item) => item.kind !== "system")
    .map((item) => `## ${item.title}\n${item.content}`)
    .join("\n\n");
  const runId = context.runId ?? `prompt_${Date.now()}_${Math.random().toString(36).slice(2, 10)}`;
  const promptText = [system, user].filter(Boolean).join("\n\n");

  return {
    templateId: template.id,
    templateVersion: template.version,
    variantId: variant.id,
    useCase: context.useCase,
    system,
    user,
    sections,
    contextSummary: {
      brandIncluded: Boolean(context.brand),
      campaignIncluded: Boolean(context.campaign),
      ragDocumentIds: context.ragDocuments?.map((doc) => doc.id) ?? [],
    },
    observability: {
      runId,
      templateId: template.id,
      templateVersion: template.version,
      variantId: variant.id,
      useCase: context.useCase,
      promptText,
      retrievedContext: context.ragDocuments ?? [],
      brandSnapshot: context.brand,
      campaignSnapshot: context.campaign,
      createdAt: new Date().toISOString(),
    },
  };
}

export function buildGenericBaselinePrompt(context: PromptBuildContext): string {
  const input = context.userInput;
  return [
    "Write marketing content for the following request.",
    section("Topic", input.topic),
    section("Brief", input.brief),
    section("Audience", input.audience),
    section("Content type", input.contentType),
    section("Channel", input.channel),
    section("Language", input.language),
    section("Tone", input.tone),
  ]
    .filter(Boolean)
    .join("\n");
}
