import { IGeminiService } from "./IGeminiService";

export class GeminiMock implements IGeminiService {
  async summarize(_text: string): Promise<string> {
    return "This is a mock summary.";
  }

  async streamSummarize(_text: string, onDelta: (chunk: string) => void): Promise<void> {
    // deterministic stream pieces to simulate streaming
    onDelta("Mock stream part 1. ");
    await new Promise((r) => setTimeout(r, 50));
    onDelta("Mock stream part 2.");
  }
}
