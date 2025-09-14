import { IGeminiService } from "./IGeminiService";
import { GoogleGenerativeAI, GenerativeModel } from "@google/generative-ai";

/**
 * GeminiService - wraps Gemini Flash 2.0 JS SDK.
 * - summarize(): one-shot summary
 * - streamSummarize(): yields partial deltas to onDelta callback
 *
 * NOTE: DO NOT hardcode API keys. Provide key when constructing this class.
 */
export class GeminiService implements IGeminiService {
  private model: GenerativeModel;

  constructor(private apiKey: string, modelName = "gemini-1.5-flash") {
    const client = new GoogleGenerativeAI(this.apiKey);
    this.model = client.getGenerativeModel({ model: modelName });
  }

  async summarize(text: string, opts?: { maxTokens?: number }): Promise<string> {
    try {
      const result = await this.model.generateContent({
        contents: [{ role: "user", parts: [{ text }] }],
        generationConfig: { maxOutputTokens: opts?.maxTokens ?? 512 },
      });
      return result.response?.text() ?? "";
    } catch (err) {
      console.error("GeminiService.summarize error", err);
      throw new Error("Gemini summarization failed");
    }
  }

  async streamSummarize(
    text: string,
    onDelta: (chunk: string) => void,
    opts?: { maxTokens?: number }
  ): Promise<void> {
    const maxRetries = 3;
    let attempt = 0;
    while (attempt < maxRetries) {
      try {
        const streamResult = await this.model.generateContentStream({
          contents: [{ role: "user", parts: [{ text }] }],
          generationConfig: { maxOutputTokens: opts?.maxTokens ?? 512 },
        });

        for await (const partial of streamResult.stream) {
          const delta = partial?.text?.() ?? "";
          if (delta) onDelta(delta);
        }
        return;
      } catch (err) {
        attempt++;
        const backoffMs = 300 * Math.pow(2, attempt);
        console.warn(`streamSummarize attempt ${attempt} failed, retrying in ${backoffMs}ms`, err);
        await new Promise((r) => setTimeout(r, backoffMs));
        if (attempt >= maxRetries) {
          console.error("streamSummarize failed after retries", err);
          throw new Error("Streaming summarization failed");
        }
      }
    }
  }
}
