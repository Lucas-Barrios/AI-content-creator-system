import { evaluateUniqueness } from "./evaluation/uniqueness";
import { buildPrompt } from "./prompt-builder/prompt-builder";
import type { PromptBuildContext } from "./prompts/types";

export const campaignPromptExample: PromptBuildContext = {
  useCase: "campaign",
  userInput: {
    language: "english",
    tone: "Professional",
    contentType: "social",
    brief: "Launch a 4-week campaign for a flexible MBA programme.",
    audience: "working professionals comparing part-time study options",
  },
  brand: {
    name: "SRH University",
    positioning: "Career-focused university for applied learning and international employability.",
    voice: "Clear, supportive, credible",
    toneGuidelines: "Professional and human. Avoid hype.",
    audienceSummary: "Prospective students and professionals evaluating next career steps.",
    approvedTerms: ["applied learning", "career outcomes", "international"],
    bannedTerms: ["guaranteed job", "cheap"],
    complianceNotes: "Do not imply guaranteed employment.",
  },
  campaign: {
    goal: "Increase MBA information-session registrations",
    offer: "Flexible MBA programme",
    audience: "working professionals",
    channels: ["linkedin", "email"],
    startDate: "2026-06-01",
    endDate: "2026-06-30",
  },
  ragDocuments: [
    {
      id: "kb_1",
      title: "Career outcomes",
      content: "SRH programmes emphasise applied projects, industry relevance, and international career preparation.",
      sourceKind: "brand",
      contentType: "program",
      language: "english",
      channel: "website",
      tags: ["career", "programme"],
      similarity: 0.84,
    },
  ],
};

export const socialPromptExample: PromptBuildContext = {
  ...campaignPromptExample,
  useCase: "social_post",
  userInput: {
    ...campaignPromptExample.userInput,
    channel: "linkedin",
    topic: "Balancing MBA study with full-time work",
  },
};

export const emailPromptExample: PromptBuildContext = {
  ...campaignPromptExample,
  useCase: "email",
  userInput: {
    ...campaignPromptExample.userInput,
    channel: "email",
    topic: "Invite prospective students to an MBA info session",
  },
};

export function buildExamplePrompt() {
  return buildPrompt(socialPromptExample);
}

export function sampleUniquenessReport() {
  const systemOutput = `For working professionals, the real MBA question is not "Can I study?" It is "Can this fit the career I am already building?"

SRH's applied learning model is designed around practical projects, international perspective, and career-relevant study. That means the programme speaks to people who need more than theory: they need learning they can connect to current decisions at work.

If you are comparing part-time MBA options, start with one filter: will the programme help you practise the work you want to do next?

Join the next information session to explore the flexible MBA path.`;

  const baselineOutput = `In today's fast-paced world, an MBA can help you take your career to the next level. Our flexible programme offers innovative solutions for professionals who want to grow. Join our information session to learn more.`;

  return evaluateUniqueness(systemOutput, baselineOutput);
}
