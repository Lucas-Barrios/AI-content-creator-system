import type { ContentType, KnowledgeBaseSource, Language, Length } from "@/lib/types";

export const contentTypeOptions: Array<{ label: string; value: ContentType; description: string }> = [
  { label: "Blog Post", value: "blog", description: "Long-form admissions and thought leadership" },
  { label: "Social Media", value: "social", description: "LinkedIn and Instagram-ready copy" },
  { label: "Program", value: "program", description: "Prospectus and landing-page descriptions" },
  { label: "Newsletter", value: "newsletter", description: "Email campaigns with CTA structure" }
];

export const topicSuggestions: Record<ContentType, string[]> = {
  blog: ["AI Ethics at SRH", "Why Study in Berlin?", "The CORE Principle", "Careers in Data Science"],
  social: ["Open Day June 2026", "New AI Programme", "Student Success Story", "Berlin Campus Life"],
  social_post: ["Open Day June 2026", "New AI Programme", "Student Success Story", "Berlin Campus Life"],
  program: ["MSc Applied Data Science and AI", "Executive MBA", "BSc Computer Science", "MSc Big Data & Analytics"],
  newsletter: ["April Campus Updates", "New Programme Launch", "Alumni Success Stories", "Open Day Invitation"],
  email: ["April Campus Updates", "New Programme Launch", "Alumni Success Stories", "Open Day Invitation"],
  ad: ["Open Day Registration", "Executive MBA Applications", "Berlin Study Advantage", "Career-Focused Learning"],
  ad_copy: ["Open Day Registration", "Executive MBA Applications", "Berlin Study Advantage", "Career-Focused Learning"]
};

export const audienceOptions = [
  "Prospective Students",
  "Current Students",
  "Faculty & Staff",
  "Industry Partners",
  "Alumni"
];

export const toneOptions = ["Academic", "Formal", "Professional", "Friendly", "Conversational"];

export const lengthOptions: Length[] = ["Short", "Medium", "Long"];

export const languageOptions: Array<{ label: string; value: Language }> = [
  { label: "English", value: "english" },
  { label: "German", value: "german" }
];

export const knowledgeBaseOptions: Array<{ label: string; value: KnowledgeBaseSource; description: string }> = [
  { label: "Hybrid", value: "hybrid", description: "Primary SRH sources plus market context" },
  { label: "Primary", value: "primary", description: "Official SRH source material only" },
  { label: "Secondary", value: "secondary", description: "Market and benchmark context only" }
];

export const defaultRequest = {
  contentType: "blog" as ContentType,
  topic: "",
  audience: "Prospective Students",
  language: "english" as Language,
  tone: "Professional",
  length: "Medium" as Length,
  knowledgeBase: "hybrid" as KnowledgeBaseSource,
  files: []
};
