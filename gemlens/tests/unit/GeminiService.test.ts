/**
 * Unit tests for GeminiService
 */

import { GeminiService } from '../../src/background/services/GeminiService';
import { GeminiMock } from '../mocks/GeminiMock';

// Mock the @google/generative-ai module
jest.mock('@google/generative-ai', () => ({
  GoogleGenerativeAI: jest.fn().mockImplementation(() => ({
    getGenerativeModel: jest.fn().mockReturnValue({
      generateContent: jest.fn().mockResolvedValue({
        response: {
          text: () => 'Mocked summary response'
        }
      }),
      generateContentStream: jest.fn().mockResolvedValue({
        stream: {
          [Symbol.asyncIterator]: async function* () {
            yield { text: () => 'Mocked ' };
            yield { text: () => 'stream ' };
            yield { text: () => 'response' };
          }
        }
      })
    })
  }))
}));

describe('GeminiService', () => {
  let service: GeminiService;
  const mockApiKey = 'AIza-mock-api-key-for-testing';

  beforeEach(() => {
    service = new GeminiService(mockApiKey);
  });

  describe('summarize', () => {
    it('should return a summary for given text', async () => {
      const text = 'This is a test article about AI and machine learning.';
      const result = await service.summarize(text);
      
      expect(result).toBe('Mocked summary response');
    });

    it('should handle maxTokens option', async () => {
      const text = 'Test content';
      const result = await service.summarize(text, { maxTokens: 256 });
      
      expect(result).toBe('Mocked summary response');
    });

    it('should throw error on API failure', async () => {
      // Mock API failure
      const failingService = new GeminiService('invalid-key');
      const mockModel = {
        generateContent: jest.fn().mockRejectedValue(new Error('API Error'))
      };
      
      // Override the model for this test
      (failingService as any).model = mockModel;
      
      await expect(failingService.summarize('test')).rejects.toThrow('Gemini summarization failed');
    });
  });

  describe('streamSummarize', () => {
    it('should stream summary chunks via callback', async () => {
      const chunks: string[] = [];
      const onDelta = (chunk: string) => chunks.push(chunk);
      
      await service.streamSummarize('Test content', onDelta);
      
      expect(chunks).toEqual(['Mocked ', 'stream ', 'response']);
    });

    it('should handle streaming errors with retry', async () => {
      const chunks: string[] = [];
      const onDelta = (chunk: string) => chunks.push(chunk);
      
      // Mock streaming failure
      const failingService = new GeminiService('invalid-key');
      const mockModel = {
        generateContentStream: jest.fn().mockRejectedValue(new Error('Stream Error'))
      };
      
      (failingService as any).model = mockModel;
      
      await expect(failingService.streamSummarize('test', onDelta)).rejects.toThrow('Streaming summarization failed');
    });
  });
});

describe('GeminiMock', () => {
  let mockService: GeminiMock;

  beforeEach(() => {
    mockService = new GeminiMock();
  });

  describe('summarize', () => {
    it('should return mock summary', async () => {
      const result = await mockService.summarize('any text');
      expect(result).toBe('This is a mock summary.');
    });
  });

  describe('streamSummarize', () => {
    it('should call onDelta with mock chunks', async () => {
      const chunks: string[] = [];
      const onDelta = (chunk: string) => chunks.push(chunk);
      
      await mockService.streamSummarize('any text', onDelta);
      
      expect(chunks).toEqual(['Mock stream part 1. ', 'Mock stream part 2.']);
    });
  });
});
