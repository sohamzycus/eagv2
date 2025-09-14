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
        const summary = await container.gemini.summarize(text);
        await container.cache.set(url, summary);
        sendResponse({ summary });
        return;
      }

      if (message.action === "streamSummarize") {
        const text: string = message.text ?? "";
        // stream via sendResponse chunks? Chrome messages don't stream — instead use runtime.connect for long-lived ports.
        // For simplicity: send a started response and then open a port to send deltas.
        sendResponse({ status: "ok" });
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
