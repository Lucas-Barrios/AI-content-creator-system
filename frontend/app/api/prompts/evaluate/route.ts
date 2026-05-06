import { NextResponse } from "next/server";

import { evaluateUniqueness } from "@/lib/ai";

interface EvaluatePromptBody {
  output?: string;
  baselineOutput?: string;
}

export async function POST(request: Request) {
  try {
    const payload = (await request.json()) as EvaluatePromptBody;
    if (!payload.output || !payload.baselineOutput) {
      return NextResponse.json({ error: "output and baselineOutput are required." }, { status: 400 });
    }

    const report = evaluateUniqueness(payload.output, payload.baselineOutput);
    return NextResponse.json({ report });
  } catch {
    return NextResponse.json({ error: "Unable to evaluate uniqueness." }, { status: 400 });
  }
}
