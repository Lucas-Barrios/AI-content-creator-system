# Uniqueness Evidence Demo

This document explains how to demonstrate that the system produces more specific, brand-aligned, and contextually relevant content than a generic ChatGPT response.

Use this for client demos, project documentation, and evaluation conversations.

## Demo Goal

Show that the AI marketing platform does not simply produce generic LLM copy. It uses:

- SRH brand profile rules
- SRH knowledge base documents
- retrieved RAG context
- prompt templates with anti-generic constraints
- uniqueness evaluation against a generic baseline
- prompt version and variant metadata

The result should be content that is more factual, more brand-specific, and safer for client-facing marketing use.

## Recommended Demo Flow

1. Choose one topic.
2. Generate a generic baseline response using vanilla ChatGPT with no knowledge base.
3. Generate the same topic using this platform.
4. Compare the outputs side by side.
5. Highlight specific evidence:
   - named programmes
   - concrete stats
   - retrieved facts
   - brand voice
   - CTA quality
   - avoided generic claims
6. Show the uniqueness score and metadata where available.

Suggested topic:

```txt
Why Choose SRH for AI and Data Science
```

Baseline prompt:

```txt
Write a blog post: Why Choose SRH for AI and Data Science
```

System prompt path:

```txt
Content type: Blog or Social
Topic: Why Choose SRH for AI and Data Science
Audience: Prospective Students
Language: English
Tone: Professional
Knowledge base: Hybrid or Primary
```

## Side-by-Side Comparison

The full raw examples are stored in:

- `examples/chatgpt_output.md`
- `examples/our_system_output.md`
- `examples/uniqueness_comparison.md`

### Evidence Table

| Evaluation Area | Generic ChatGPT | Our System | Why It Matters |
|---|---|---|---|
| CORE learning model | Mentions CORE generally | Uses 5-week block structure and 8 ECTS cap | Specific retrieved details are harder to hallucinate and more useful to students |
| Career support | Describes internships and networks generically | Names Career:Skills and alumni support | Shows institutional specificity |
| International audience | Says SRH has diversity | Cites students from 140+ countries | Concrete proof is more persuasive than broad claims |
| Alumni proof | No named alumni proof | Uses named alumni quote with role and company | Stronger social proof and better conversion value |
| Industry context | Lists possible employers, including unverified names | Frames SAP and Accenture as curriculum partners | Reduces hallucination risk and improves factual grounding |
| CTA | Ends with a generic summary | Gives clear actions: apply or attend open day | Better demo and marketing readiness |

## Example Excerpts

### Generic ChatGPT

```txt
Artificial Intelligence and Data Science are reshaping industries—from healthcare and finance to consulting and entrepreneurship. Choosing the right university is therefore a strategic decision.
```

Problem:

- Broad industry opener
- Could apply to any university
- No SRH-specific proof
- No retrieved context

### Our System

```txt
SRH's curriculum is structured around intensive 5-week blocks, allowing students to immerse themselves deeply in subjects such as Machine Learning, Data Engineering, and AI Vision. With a cap of just 8 ECTS credits per block, the workload is manageable...
```

Why this is stronger:

- Includes specific SRH academic structure
- Uses concrete numbers
- Connects the fact to student benefit
- Demonstrates RAG-grounded generation

## Brand Alignment Evidence

The system is designed to align with SRH-specific brand requirements:

| Brand Requirement | Evidence in System Output |
|---|---|
| Professional but human tone | Explains practical benefits without exaggerated hype |
| Student-first perspective | Frames SRH details around student decisions and outcomes |
| British English | Uses forms like `recognising` and `prioritises` |
| Avoid unsupported claims | Uses knowledge-base details instead of invented employer lists |
| Clear CTA | Directs readers to apply or attend an open day |

## Contextual Relevance Evidence

The system output is more contextually relevant because it uses retrieved knowledge, not only model memory.

Examples of retrieved/contextual details:

- 5-week CORE block structure
- 8 ECTS block cap
- Career:Skills programme
- 140+ countries represented
- named alumni quote
- SAP and Accenture partnership context
- SRH Career Center and alumni network

These details create a stronger answer for a prospective student because they answer the real decision question:

```txt
Why should I trust this university for my future career?
```

## Strategies Used To Ensure Uniqueness

### 1. Retrieval-Augmented Generation

The system retrieves relevant knowledge-base chunks before generation. This gives the model access to internal or curated facts that generic ChatGPT does not have.

### 2. Brand Profile Injection

Brand profiles guide:

- positioning
- voice
- tone
- approved terminology
- banned terminology
- audience summary
- compliance notes

### 3. Anti-Generic Prompt Constraints

The TypeScript prompt framework includes a distinctiveness block that discourages vague phrases such as:

- `in today's fast-paced world`
- `unlock your potential`
- `take it to the next level`
- `game-changer`
- `innovative solutions`
- `drive growth`
- `elevate your brand`

### 4. Multi-Step Prompt Orchestration

The new framework can run:

1. Strategy generation
2. Messaging angle selection
3. Content generation
4. Refinement
5. Evaluation

This makes the final answer more deliberate than a single generic prompt.

### 5. Baseline Comparison

The system can compare its output to a generic baseline using:

- cosine similarity
- lexical diversity
- sentence variation
- distinct term ratio
- generic phrase count

### 6. Prompt Versioning

Prompt outputs can include metadata:

```json
{
  "framework": "ts-prompt-framework",
  "promptRunId": "...",
  "templateId": "social-post",
  "templateVersion": "1.0.0",
  "variantId": "precision-v1",
  "uniquenessScore": 71,
  "baselineSimilarity": 0.4775,
  "ragContextUsed": true,
  "brandProfileUsed": true
}
```

This gives reproducibility and makes quality improvement measurable over time.

## Demo Scorecard

Use this table during the presentation:

| Criterion | Generic ChatGPT | Our System |
|---|:---:|:---:|
| Uses retrieved SRH facts | No | Yes |
| Includes exact academic structure | No | Yes |
| Includes named social proof | No | Yes |
| Avoids unsupported employer claims | No | Yes |
| Matches SRH voice | Partial | Strong |
| Gives concrete CTA | Weak | Strong |
| Tracks prompt version | No | Yes |
| Provides uniqueness metrics | No | Yes |

## Recommended Client Demo Script

```txt
First, we generate the same topic with a generic model prompt. The result sounds polished, but it is broad and could describe many universities.

Now we generate with our system. The difference is that the answer uses SRH-specific knowledge: the CORE model structure, Career:Skills, international student body, alumni proof, and specific programme context.

This is the value of the platform: it does not just write faster. It writes with memory, brand consistency, and evidence. We can also measure how different the output is from a generic baseline using the uniqueness score and related metrics.
```

## Known Caveat

The current example still shows one weakness: both the generic baseline and older system output open with a broad industry trend sentence.

This is already addressed in the newer TypeScript prompt framework through anti-generic constraints. For future demos, prefer generating a fresh example with the TS prompt framework enabled:

```env
ENABLE_TS_PROMPT_FRAMEWORK=true
TS_PROMPT_FRAMEWORK_MODE=social_only
```

Then use `compareWithLegacy: true` or `/api/prompts/evaluate` to produce updated comparison metrics.
