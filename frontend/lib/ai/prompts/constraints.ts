export const GENERIC_MARKETING_PHRASES = [
  "in today's fast-paced world",
  "unlock your potential",
  "take it to the next level",
  "game-changer",
  "cutting-edge",
  "seamless experience",
  "innovative solutions",
  "tailored solutions",
  "empower your business",
  "drive growth",
  "elevate your brand",
  "transform your business",
  "stand out from the crowd",
  "like never before",
  "one-stop shop",
] as const;

export const DISTINCTIVENESS_BLOCK = `Distinctiveness requirements:
- Do not use vague marketing phrases, including: ${GENERIC_MARKETING_PHRASES.join(", ")}.
- Name the audience directly and write for their actual decision context.
- Include at least one concrete situation, example, trade-off, or proof point from the supplied context.
- Make the positioning opinionated: state what the audience should do differently, not just what the product/brand offers.
- Vary sentence length and rhythm. Avoid a uniform list of short promotional statements.
- Prefer specific nouns and verbs over abstract claims like "quality", "innovation", "success", or "solutions".
- If context is missing, say what assumption you are making instead of inventing facts.
- Never invent statistics, accreditations, testimonials, deadlines, or guarantees.`;

export const QUALITY_BAR_BLOCK = `Quality bar:
- The output must feel written for this brand, this audience, and this channel.
- Every claim must be supported by brand, campaign, user, or retrieved knowledge context.
- CTAs must be direct and channel-appropriate.
- Remove filler before returning the final answer.
- Return only the requested output format.`;

export function countGenericPhrases(text: string): number {
  const normalized = text.toLowerCase();
  return GENERIC_MARKETING_PHRASES.reduce((count, phrase) => {
    return normalized.includes(phrase) ? count + 1 : count;
  }, 0);
}
