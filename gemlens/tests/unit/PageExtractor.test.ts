/**
 * Unit tests for PageExtractor functionality
 */

import { extractTextFromHtml, isYouTubePage, simpleHash } from '../../src/shared/utils';

// Mock DOM environment
const mockDocument = {
  createElement: jest.fn(),
  title: 'Test Page Title',
  body: {
    cloneNode: jest.fn(),
    innerHTML: '<div>Test content</div>'
  },
  querySelector: jest.fn(),
  querySelectorAll: jest.fn()
};

const mockWindow = {
  location: {
    href: 'https://example.com/test',
    hostname: 'example.com'
  }
};

// Setup DOM mocks
(global as any).document = mockDocument;
(global as any).window = mockWindow;

describe('PageExtractor Utils', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('extractTextFromHtml', () => {
    it('should extract text content from HTML', () => {
      const mockDiv = {
        innerHTML: '',
        textContent: 'This is extracted text content',
        innerText: 'This is extracted text content'
      };

      mockDocument.createElement.mockReturnValue(mockDiv);

      const html = '<div><p>This is extracted text content</p></div>';
      const result = extractTextFromHtml(html);

      expect(result).toBe('This is extracted text content');
      expect(mockDocument.createElement).toHaveBeenCalledWith('div');
    });

    it('should handle empty HTML', () => {
      const mockDiv = {
        innerHTML: '',
        textContent: '',
        innerText: ''
      };

      mockDocument.createElement.mockReturnValue(mockDiv);

      const result = extractTextFromHtml('');

      expect(result).toBe('');
    });

    it('should fallback to innerText if textContent is empty', () => {
      const mockDiv = {
        innerHTML: '',
        textContent: '',
        innerText: 'Fallback text'
      };

      mockDocument.createElement.mockReturnValue(mockDiv);

      const result = extractTextFromHtml('<div>Some HTML</div>');

      expect(result).toBe('Fallback text');
    });
  });

  describe('isYouTubePage', () => {
    it('should return true for YouTube URLs', () => {
      (mockWindow.location as any).hostname = 'www.youtube.com';
      expect(isYouTubePage()).toBe(true);

      (mockWindow.location as any).hostname = 'youtube.com';
      expect(isYouTubePage()).toBe(true);

      (mockWindow.location as any).hostname = 'm.youtube.com';
      expect(isYouTubePage()).toBe(true);
    });

    it('should return false for non-YouTube URLs', () => {
      (mockWindow.location as any).hostname = 'example.com';
      expect(isYouTubePage()).toBe(false);

      (mockWindow.location as any).hostname = 'google.com';
      expect(isYouTubePage()).toBe(false);

      (mockWindow.location as any).hostname = 'notyoutube.com';
      expect(isYouTubePage()).toBe(false);
    });
  });

  describe('simpleHash', () => {
    it('should generate consistent hash for same input', () => {
      const text = 'This is a test string for hashing';
      const hash1 = simpleHash(text);
      const hash2 = simpleHash(text);

      expect(hash1).toBe(hash2);
      expect(typeof hash1).toBe('string');
      expect(hash1.length).toBeGreaterThan(0);
    });

    it('should generate different hashes for different inputs', () => {
      const text1 = 'First test string';
      const text2 = 'Second test string';
      
      const hash1 = simpleHash(text1);
      const hash2 = simpleHash(text2);

      expect(hash1).not.toBe(hash2);
    });

    it('should handle empty string', () => {
      const hash = simpleHash('');
      expect(typeof hash).toBe('string');
      expect(hash).toBe('0');
    });

    it('should generate alphanumeric hash', () => {
      const hash = simpleHash('test content');
      expect(hash).toMatch(/^[a-z0-9]+$/);
    });
  });
});

// Mock PageExtractor class tests
describe('PageExtractor Integration', () => {
  beforeEach(() => {
    // Reset mocks
    jest.clearAllMocks();
    
    // Setup default DOM structure
    mockDocument.querySelector.mockImplementation((selector) => {
      if (selector === 'article') {
        return {
          innerHTML: '<h1>Article Title</h1><p>Article content goes here.</p>'
        };
      }
      if (selector === 'main') {
        return {
          innerHTML: '<div>Main content area</div>'
        };
      }
      return null;
    });

    mockDocument.querySelectorAll.mockReturnValue([]);
  });

  it('should extract content from article tag', () => {
    const mockDiv = {
      innerHTML: '',
      textContent: 'Article Title Article content goes here.',
      innerText: 'Article Title Article content goes here.'
    };

    mockDocument.createElement.mockReturnValue(mockDiv);

    // Simulate content extraction logic
    const articleElement = mockDocument.querySelector('article');
    expect(articleElement).toBeTruthy();
    
    if (articleElement) {
      const text = extractTextFromHtml(articleElement.innerHTML);
      expect(text).toBe('Article Title Article content goes here.');
    }
  });

  it('should fallback to main tag if no article', () => {
    // Mock no article found
    mockDocument.querySelector.mockImplementation((selector) => {
      if (selector === 'article') return null;
      if (selector === 'main') {
        return {
          innerHTML: '<div>Main content area</div>'
        };
      }
      return null;
    });

    const mockDiv = {
      innerHTML: '',
      textContent: 'Main content area',
      innerText: 'Main content area'
    };

    mockDocument.createElement.mockReturnValue(mockDiv);

    const mainElement = mockDocument.querySelector('main');
    expect(mainElement).toBeTruthy();
    
    if (mainElement) {
      const text = extractTextFromHtml(mainElement.innerHTML);
      expect(text).toBe('Main content area');
    }
  });

  it('should handle YouTube page detection', () => {
    (mockWindow.location as any).hostname = 'www.youtube.com';
    expect(isYouTubePage()).toBe(true);
  });
});
