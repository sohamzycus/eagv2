import { GeminiService } from "./services/GeminiService";
import { GeminiMock } from "./services/GeminiMock";
import { StorageService } from "./services/StorageService";
import { CacheService } from "./services/CacheService";
import { IGeminiService } from "./services/IGeminiService";

export interface Container {
  gemini: IGeminiService;
  storage: StorageService;
  cache: CacheService;
}

/**
 * buildContainer - builds runtime container.
 * If USE_REAL_API env is provided (service worker can read runtime.getManifest or similar),
 * you'll still rely on StorageService for the API key. For tests, import this file and call buildContainer(true) to use GeminiMock.
 */
export function buildContainer(useMock = false, apiKey?: string): Container {
  const storage = new StorageService();
  const cache = new CacheService();
  let gemini: IGeminiService;

  if (useMock) gemini = new GeminiMock();
  else {
    if (!apiKey) {
      // Construct a placeholder—actual service_worker will call storage.getApiKey() then recompose if needed.
      gemini = new GeminiMock();
    } else gemini = new GeminiService(apiKey);
  }

  return { gemini, storage, cache };
}
