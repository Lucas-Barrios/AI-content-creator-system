import { countGenericPhrases } from "../prompts/constraints";
import type { PromptEvaluationCandidate, PromptVariant, UniquenessReport } from "../prompts/types";

const WORD_PATTERN = /[\p{L}\p{N}']+/gu;

function tokenize(text: string): string[] {
  return text.toLowerCase().match(WORD_PATTERN) ?? [];
}

function splitSentences(text: string): string[] {
  return text
    .split(/[.!?]+/)
    .map((sentence) => sentence.trim())
    .filter(Boolean);
}

export function lexicalDiversity(text: string): number {
  const tokens = tokenize(text);
  if (tokens.length === 0) return 0;
  return new Set(tokens).size / tokens.length;
}

export function sentenceVariation(text: string): number {
  const lengths = splitSentences(text).map((sentence) => tokenize(sentence).length);
  if (lengths.length < 2) return 0;
  const average = lengths.reduce((sum, value) => sum + value, 0) / lengths.length;
  const variance = lengths.reduce((sum, value) => sum + Math.pow(value - average, 2), 0) / lengths.length;
  return Math.min(1, Math.sqrt(variance) / Math.max(average, 1));
}

export function cosineSimilarityFromText(a: string, b: string): number {
  const aTokens = tokenize(a);
  const bTokens = tokenize(b);
  const vocabulary = new Set([...aTokens, ...bTokens]);
  if (vocabulary.size === 0) return 0;

  const aCounts = new Map<string, number>();
  const bCounts = new Map<string, number>();
  for (const token of aTokens) aCounts.set(token, (aCounts.get(token) ?? 0) + 1);
  for (const token of bTokens) bCounts.set(token, (bCounts.get(token) ?? 0) + 1);

  let dot = 0;
  let aMagnitude = 0;
  let bMagnitude = 0;
  for (const token of vocabulary) {
    const av = aCounts.get(token) ?? 0;
    const bv = bCounts.get(token) ?? 0;
    dot += av * bv;
    aMagnitude += av * av;
    bMagnitude += bv * bv;
  }

  if (aMagnitude === 0 || bMagnitude === 0) return 0;
  return dot / (Math.sqrt(aMagnitude) * Math.sqrt(bMagnitude));
}

export function distinctTermRatio(output: string, baseline: string): number {
  const baselineTerms = new Set(tokenize(baseline));
  const outputTerms = tokenize(output);
  if (outputTerms.length === 0) return 0;
  const distinctTerms = outputTerms.filter((token) => !baselineTerms.has(token));
  return distinctTerms.length / outputTerms.length;
}

export function evaluateUniqueness(output: string, baselineOutput: string): UniquenessReport {
  const cosineSimilarity = cosineSimilarityFromText(output, baselineOutput);
  const outputLexicalDiversity = lexicalDiversity(output);
  const baselineLexicalDiversity = lexicalDiversity(baselineOutput);
  const outputSentenceVariation = sentenceVariation(output);
  const baselineSentenceVariation = sentenceVariation(baselineOutput);
  const outputGenericPhraseCount = countGenericPhrases(output);
  const baselineGenericPhraseCount = countGenericPhrases(baselineOutput);
  const termRatio = distinctTermRatio(output, baselineOutput);

  const similarityComponent = (1 - cosineSimilarity) * 38;
  const diversityComponent = Math.min(1, outputLexicalDiversity / Math.max(baselineLexicalDiversity, 0.01)) * 20;
  const sentenceComponent = Math.min(1, outputSentenceVariation / Math.max(baselineSentenceVariation, 0.1)) * 16;
  const distinctTermComponent = termRatio * 18;
  const clichéPenalty = Math.min(18, outputGenericPhraseCount * 6);
  const score = Math.max(0, Math.min(100, similarityComponent + diversityComponent + sentenceComponent + distinctTermComponent + 8 - clichéPenalty));

  const notes = [
    cosineSimilarity > 0.82 ? "Output is very close to the generic baseline." : "Output separates from the generic baseline.",
    outputGenericPhraseCount > 0 ? "Generic phrases detected; refine before client use." : "No tracked generic phrases detected.",
    termRatio < 0.28 ? "Distinct term ratio is low; add more brand/context-specific language." : "Distinct term ratio is acceptable.",
  ];

  return {
    score: Math.round(score),
    cosineSimilarity: Number(cosineSimilarity.toFixed(4)),
    lexicalDiversity: Number(outputLexicalDiversity.toFixed(4)),
    baselineLexicalDiversity: Number(baselineLexicalDiversity.toFixed(4)),
    sentenceVariation: Number(outputSentenceVariation.toFixed(4)),
    baselineSentenceVariation: Number(baselineSentenceVariation.toFixed(4)),
    distinctTermRatio: Number(termRatio.toFixed(4)),
    genericPhraseCount: outputGenericPhraseCount,
    baselineGenericPhraseCount: baselineGenericPhraseCount,
    recommendation: score >= 72 && outputGenericPhraseCount === 0 ? "use" : score >= 58 ? "refine" : "reject",
    notes,
  };
}

export function selectBestVariant(candidates: PromptEvaluationCandidate[]): {
  variant: PromptVariant;
  report: UniquenessReport;
} {
  if (candidates.length === 0) {
    throw new Error("At least one prompt variant candidate is required.");
  }

  return candidates
    .map((candidate) => ({
      variant: candidate.variant,
      report: evaluateUniqueness(candidate.output, candidate.baselineOutput),
    }))
    .sort((a, b) => b.report.score - a.report.score)[0];
}
