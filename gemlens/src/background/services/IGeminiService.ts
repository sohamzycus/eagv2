export interface IGeminiService {
  summarize(text: string, opts?: { maxTokens?: number }): Promise<string>;
  streamSummarize(
    text: string,
    onDelta: (chunk: string) => void,
    opts?: { maxTokens?: number }
  ): Promise<void>;
}
