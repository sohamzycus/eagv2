export class StorageService {
  private API_KEY_KEY = "GEMINI_API_KEY";

  async getApiKey(): Promise<string | null> {
    return new Promise((resolve) => {
      chrome.storage.local.get([this.API_KEY_KEY], (res) => {
        resolve(res[this.API_KEY_KEY] ?? null);
      });
    });
  }

  async setApiKey(key: string): Promise<void> {
    return new Promise((resolve) => {
      chrome.storage.local.set({ [this.API_KEY_KEY]: key }, () => resolve());
    });
  }

  async clearApiKey(): Promise<void> {
    return new Promise((resolve) => {
      chrome.storage.local.remove([this.API_KEY_KEY], () => resolve());
    });
  }
}
