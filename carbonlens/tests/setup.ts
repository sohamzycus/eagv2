/**
 * Jest setup file for CarbonLens tests
 */

// Mock Chrome APIs
const mockChrome = {
  storage: {
    local: {
      get: jest.fn((keys, callback) => {
        callback({});
      }),
      set: jest.fn((items, callback) => {
        if (callback) callback();
      }),
      remove: jest.fn((keys, callback) => {
        if (callback) callback();
      }),
    },
  },
  runtime: {
    sendMessage: jest.fn(),
    connect: jest.fn(),
    onMessage: {
      addListener: jest.fn(),
    },
    onConnect: {
      addListener: jest.fn(),
    },
    lastError: null,
  },
  scripting: {
    executeScript: jest.fn(),
  },
  tabs: {
    query: jest.fn(),
  },
};

// Make chrome available globally
(global as any).chrome = mockChrome;

// Mock fetch for API calls
global.fetch = jest.fn();

// Mock console methods to reduce test noise
global.console = {
  ...console,
  log: jest.fn(),
  warn: jest.fn(),
  error: jest.fn(),
};
