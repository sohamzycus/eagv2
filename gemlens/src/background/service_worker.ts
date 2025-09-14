import { buildContainer } from "./di";
import { GeminiService } from "./services/GeminiService";
import { GeminiMock } from "./services/GeminiMock";

let container = buildContainer(true); // start with mock

// Recompose with real API if key exists
(async function init() {
  const storage = container.storage;
  const key = await storage.getApiKey();
  if (key) {
    container = buildContainer(false, key);
  }
})();

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  (async () => {
    try {
      if (message.action === "summarizePage") {
        const url = message.url ?? (sender.tab && sender.tab.url) ?? "unknown";
        const cached = await container.cache.get(url);
        if (cached) {
          sendResponse({ summary: cached });
          return;
        }

        const text: string = message.text ?? "";
        if (!text || text.length < 50) {
          sendResponse({ error: "Not enough content to summarize" });
          return;
        }

        // Request longer summary with specific instructions
        const prompt = `Please provide a comprehensive summary of the following content. The summary should be detailed and include:
        - Main topics and key points
        - Important details and context
        - Any conclusions or recommendations
        - Structure the summary in clear paragraphs
        - Aim for at least 10-15 sentences to capture all important information
        
        Content to summarize:
        ${text}`;

        const summary = await container.gemini.summarize(prompt, { maxTokens: 1024 });
        
        // Store in history
        await container.storage.addToHistory({
          url,
          title: message.title || 'Untitled Page',
          summary,
          timestamp: Date.now(),
          type: message.type || 'webpage'
        });
        
        await container.cache.set(url, summary);
        
        // Update badge to show completion
        chrome.action.setBadgeText({ text: '✓' });
        chrome.action.setBadgeBackgroundColor({ color: '#34C759' });
        setTimeout(() => {
          chrome.action.setBadgeText({ text: '' });
        }, 3000);
        
        sendResponse({ summary });
        return;
      }

      if (message.action === "streamSummarize") {
        const text: string = message.text ?? "";
        // stream via sendResponse chunks? Chrome messages don't stream — instead use runtime.connect for long-lived ports.
        // For simplicity: send a started response and then open a port to send deltas.
        sendResponse({ status: "ok" });
      }

      if (message.action === "checkApiKey") {
        // Check if API key exists
        const key = await container.storage.getApiKey();
        sendResponse({ hasKey: !!key, isValid: !!key });
        return;
      }

      if (message.action === "getHistory") {
        // Get summary history
        const history = await container.storage.getHistory();
        sendResponse({ history });
        return;
      }

      if (message.action === "refreshApiKey") {
        // Recompose container when API key changed in Options page
        const key = await container.storage.getApiKey();
        if (key) container = buildContainer(false, key);
        sendResponse({ ok: true });
        return;
      }
    } catch (err) {
      console.error("service_worker message handler error", err);
      sendResponse({ error: (err as Error).message ?? "Unknown error" });
    }
  })();
  return true; // indicate async
});

// Handle streaming connections
chrome.runtime.onConnect.addListener((port) => {
  if (port.name === "gemini-stream") {
    port.onMessage.addListener(async (message) => {
      if (message.action === "streamSummarize") {
        try {
          const text: string = message.text ?? "";
          await container.gemini.streamSummarize(text, (chunk: string) => {
            port.postMessage({ type: "delta", chunk });
          });
          port.postMessage({ type: "complete" });
        } catch (err) {
          port.postMessage({ type: "error", error: (err as Error).message });
        }
      }
    });
  }
});
