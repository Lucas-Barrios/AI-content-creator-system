import { NextResponse } from "next/server";

import { buildPrompt } from "@/lib/ai";
import type { PromptBuildContext } from "@/lib/ai";

export async function POST(request: Request) {
  try {
    const payload = (await request.json()) as PromptBuildContext;
    if (!payload.useCase || !payload.userInput?.language) {
      return NextResponse.json({ error: "useCase and userInput.language are required." }, { status: 400 });
    }

    const prompt = buildPrompt(payload);
    return NextResponse.json({ prompt });
  } catch (error) {
    const message = error instanceof Error ? error.message : "Unable to build prompt.";
    return NextResponse.json({ error: message }, { status: 400 });
  }
}
