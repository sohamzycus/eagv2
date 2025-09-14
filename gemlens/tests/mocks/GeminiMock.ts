import { IGeminiService } from "../../src/background/services/IGeminiService";

export class GeminiMock implements IGeminiService {
  async summarize(_text: string): Promise<string> {
    return "This is a mock summary.";
  }
  async streamSummarize(_text: string, onDelta: (chunk: string) => void): Promise<void> {
    onDelta("Mock stream part 1. ");
    await new Promise((r) => setTimeout(r, 10));
    onDelta("Mock stream part 2.");
  }
}
