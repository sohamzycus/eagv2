interface SummaryHistoryItem {
  url: string;
  title: string;
  summary: string;
  timestamp: number;
  type: 'webpage' | 'video';
}

export class StorageService {
  private API_KEY_KEY = "GEMINI_API_KEY";
  private HISTORY_KEY = "SUMMARY_HISTORY";
  private MAX_HISTORY_ITEMS = 50;

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

  async addToHistory(item: SummaryHistoryItem): Promise<void> {
    return new Promise((resolve) => {
      chrome.storage.local.get([this.HISTORY_KEY], (res) => {
        const history: SummaryHistoryItem[] = res[this.HISTORY_KEY] || [];
        
        // Add new item to the beginning
        history.unshift(item);
        
        // Keep only the last 50 items
        if (history.length > this.MAX_HISTORY_ITEMS) {
          history.splice(this.MAX_HISTORY_ITEMS);
        }
        
        chrome.storage.local.set({ [this.HISTORY_KEY]: history }, () => resolve());
      });
    });
  }

  async getHistory(): Promise<SummaryHistoryItem[]> {
    return new Promise((resolve) => {
      chrome.storage.local.get([this.HISTORY_KEY], (res) => {
        resolve(res[this.HISTORY_KEY] || []);
      });
    });
  }

  async clearHistory(): Promise<void> {
    return new Promise((resolve) => {
      chrome.storage.local.remove([this.HISTORY_KEY], () => resolve());
    });
  }
}
