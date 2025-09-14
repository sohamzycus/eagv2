type CacheEntry = { createdAt: number; ttl: number; value: any };

export class CacheService {
  private KEY_PREFIX = "GEMLENS_CACHE_";
  private defaultTtl = 24 * 60 * 60 * 1000; // 24 hours

  private storageKey(url: string) {
    return `${this.KEY_PREFIX}${encodeURIComponent(url)}`;
  }

  async get(url: string): Promise<any | null> {
    return new Promise((resolve) => {
      chrome.storage.local.get([this.storageKey(url)], (res) => {
        const entry: CacheEntry = res[this.storageKey(url)];
        if (!entry) return resolve(null);
        if (Date.now() - entry.createdAt > (entry.ttl ?? this.defaultTtl)) {
          // expired
          chrome.storage.local.remove([this.storageKey(url)], () => resolve(null));
        } else resolve(entry.value);
      });
    });
  }

  async set(url: string, value: any, ttlMs?: number): Promise<void> {
    const entry: CacheEntry = { createdAt: Date.now(), ttl: ttlMs ?? this.defaultTtl, value };
    return new Promise((resolve) => {
      chrome.storage.local.set({ [this.storageKey(url)]: entry }, () => resolve());
    });
  }

  async invalidate(url: string): Promise<void> {
    return new Promise((resolve) => {
      chrome.storage.local.remove([this.storageKey(url)], () => resolve());
    });
  }
}
