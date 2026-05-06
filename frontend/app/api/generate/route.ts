import { NextResponse } from "next/server";

import { GenerationRouter } from "@/lib/generation/generation-router";
import type { GenerateRequest } from "@/lib/types";

export const runtime = "nodejs";

export async function POST(request: Request) {
  let payload: GenerateRequest;
  try {
    payload = (await request.json()) as GenerateRequest;
  } catch {
    return NextResponse.json({ error: "Invalid JSON body." }, { status: 400 });
  }

  if (!payload.topic?.trim()) {
    return NextResponse.json({ error: "Topic is required." }, { status: 400 });
  }

  try {
    const response = await new GenerationRouter().generate(payload);
    return NextResponse.json(response);
  } catch (error) {
    return NextResponse.json(
      {
        error: "Content generation failed.",
        detail: error instanceof Error ? error.message : "Unknown generation error.",
      },
      { status: 502 },
    );
  }
}
