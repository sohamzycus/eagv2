/**
 * Unit tests for CacheService
 */

import { CacheService } from '../../src/background/services/CacheService';

// Mock chrome.storage.local
const mockStorage = {
  get: jest.fn(),
  set: jest.fn(),
  remove: jest.fn()
};

// Mock chrome API
(global as any).chrome = {
  storage: {
    local: mockStorage
  }
};

describe('CacheService', () => {
  let cacheService: CacheService;
  const testUrl = 'https://example.com/test-page';
  const testValue = { summary: 'Test summary content' };

  beforeEach(() => {
    cacheService = new CacheService();
    jest.clearAllMocks();
  });

  describe('set', () => {
    it('should store value with default TTL', async () => {
      mockStorage.set.mockImplementation((data, callback) => callback());

      await cacheService.set(testUrl, testValue);

      expect(mockStorage.set).toHaveBeenCalledWith(
        expect.objectContaining({
          'GEMLENS_CACHE_https%3A%2F%2Fexample.com%2Ftest-page': expect.objectContaining({
            value: testValue,
            createdAt: expect.any(Number),
            ttl: 24 * 60 * 60 * 1000 // 24 hours
          })
        }),
        expect.any(Function)
      );
    });

    it('should store value with custom TTL', async () => {
      const customTtl = 60 * 60 * 1000; // 1 hour
      mockStorage.set.mockImplementation((data, callback) => callback());

      await cacheService.set(testUrl, testValue, customTtl);

      expect(mockStorage.set).toHaveBeenCalledWith(
        expect.objectContaining({
          'GEMLENS_CACHE_https%3A%2F%2Fexample.com%2Ftest-page': expect.objectContaining({
            value: testValue,
            ttl: customTtl
          })
        }),
        expect.any(Function)
      );
    });
  });

  describe('get', () => {
    it('should return cached value if not expired', async () => {
      const cacheEntry = {
        createdAt: Date.now() - 1000, // 1 second ago
        ttl: 24 * 60 * 60 * 1000, // 24 hours
        value: testValue
      };

      mockStorage.get.mockImplementation((keys, callback) => {
        callback({
          'GEMLENS_CACHE_https%3A%2F%2Fexample.com%2Ftest-page': cacheEntry
        });
      });

      const result = await cacheService.get(testUrl);

      expect(result).toEqual(testValue);
    });

    it('should return null if cache entry does not exist', async () => {
      mockStorage.get.mockImplementation((keys, callback) => callback({}));

      const result = await cacheService.get(testUrl);

      expect(result).toBeNull();
    });

    it('should remove and return null if cache entry is expired', async () => {
      const expiredEntry = {
        createdAt: Date.now() - 25 * 60 * 60 * 1000, // 25 hours ago
        ttl: 24 * 60 * 60 * 1000, // 24 hours TTL
        value: testValue
      };

      mockStorage.get.mockImplementation((keys, callback) => {
        callback({
          'GEMLENS_CACHE_https%3A%2F%2Fexample.com%2Ftest-page': expiredEntry
        });
      });
      mockStorage.remove.mockImplementation((keys, callback) => callback());

      const result = await cacheService.get(testUrl);

      expect(result).toBeNull();
      expect(mockStorage.remove).toHaveBeenCalledWith(
        ['GEMLENS_CACHE_https%3A%2F%2Fexample.com%2Ftest-page'],
        expect.any(Function)
      );
    });
  });

  describe('invalidate', () => {
    it('should remove cache entry for given URL', async () => {
      mockStorage.remove.mockImplementation((keys, callback) => callback());

      await cacheService.invalidate(testUrl);

      expect(mockStorage.remove).toHaveBeenCalledWith(
        ['GEMLENS_CACHE_https%3A%2F%2Fexample.com%2Ftest-page'],
        expect.any(Function)
      );
    });
  });

  describe('storageKey', () => {
    it('should properly encode URLs for storage keys', async () => {
      const complexUrl = 'https://example.com/path?param=value&other=test#section';
      mockStorage.set.mockImplementation((data, callback) => callback());

      await cacheService.set(complexUrl, testValue);

      const expectedKey = 'GEMLENS_CACHE_https%3A%2F%2Fexample.com%2Fpath%3Fparam%3Dvalue%26other%3Dtest%23section';
      expect(mockStorage.set).toHaveBeenCalledWith(
        expect.objectContaining({
          [expectedKey]: expect.any(Object)
        }),
        expect.any(Function)
      );
    });
  });
});
