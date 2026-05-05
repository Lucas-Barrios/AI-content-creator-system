export type ContentType = "blog" | "social" | "program" | "newsletter";
export type Language = "english" | "german";
export type KnowledgeBaseSource = "hybrid" | "primary" | "secondary";
export type Length = "Short" | "Medium" | "Long";

export interface SourceFile {
  filename: string;
  words: number;
  source: "primary" | "secondary";
}

export interface GenerateRequest {
  contentType: ContentType;
  topic: string;
  audience: string;
  language: Language;
  tone: string;
  length: Length;
  knowledgeBase: KnowledgeBaseSource;
  files?: UploadedFile[];
  feedback?: string;
  previousContent?: string;
}

export interface UploadedFile {
  id: string;
  name: string;
  size: number;
  contentType: string;
  url?: string;
}

export interface GenerateResponse {
  content: string;
  sources: SourceFile[];
  metadata: {
    topic: string;
    contentType: ContentType;
    language: Language;
    tone: string;
    length: Length;
    knowledgeBase: KnowledgeBaseSource;
      wordCount: number;
      generatedAt: string;
      generationId: string;
  };
}

export type FeedbackStatus = "approved" | "needs_revision";

export interface FeedbackRequest {
  generationId: string;
  status: FeedbackStatus;
  comment: string;
  request: GenerateRequest;
  response: GenerateResponse;
}

export interface FeedbackResponse {
  id: string;
  generationId: string;
  status: FeedbackStatus;
  createdAt: string;
}

export interface ApiErrorBody {
  error: string;
  detail?: string;
  status?: number;
}

export interface HistoryItem {
  id: string;
  request: GenerateRequest;
  response: GenerateResponse;
}
