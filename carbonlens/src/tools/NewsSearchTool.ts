/**
 * News search tool for carbon/climate related news
 */

import { BaseToolAdapter } from './ToolAdapter';
import type { ToolResult } from '@/shared/types';
import { retryWithBackoff } from '@/shared/utils';

interface NewsArticle {
  title: string;
  description: string;
  url: string;
  source: string;
  publishedAt: string;
  relevanceScore?: number;
}

export class NewsSearchTool extends BaseToolAdapter {
  public readonly name = 'NewsSearchTool';
  public readonly description = 'Search for recent carbon/climate news and reports';
  public readonly schema = {
    type: 'object',
    properties: {
      query: {
        type: 'string',
        description: 'Search query for news articles',
      },
      category: {
        type: 'string',
        description: 'News category filter',
        enum: ['carbon', 'climate', 'renewable', 'emissions', 'sustainability', 'policy'],
      },
      days: {
        type: 'integer',
        description: 'Number of days to look back',
        minimum: 1,
        maximum: 30,
        default: 7,
      },
      limit: {
        type: 'integer',
        description: 'Maximum number of articles to return',
        minimum: 1,
        maximum: 50,
        default: 10,
      },
    },
    required: ['query'],
  };

  constructor(
    private backendUrl?: string,
    private apiKey?: string,
    private useMock: boolean = true
  ) {
    super();
  }

  public async execute(args: Record<string, any>): Promise<ToolResult> {
    if (!this.validateArgs(args)) {
      return this.createErrorResult('Invalid arguments provided');
    }

    const { query, category, days = 7, limit = 10 } = args;

    try {
      if (this.useMock) {
        return this.getMockNews(query, category, days, limit);
      }

      if (this.backendUrl) {
        return await this.queryViaBackend(query, category, days, limit);
      } else {
        return this.createErrorResult('No backend URL configured for news search');
      }
    } catch (error) {
      return this.createErrorResult(`News search failed: ${(error as Error).message}`);
    }
  }

  private async queryViaBackend(
    query: string,
    category: string,
    days: number,
    limit: number
  ): Promise<ToolResult> {
    const response = await retryWithBackoff(async () => {
      const res = await fetch(`${this.backendUrl}/api/news/search`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query, category, days, limit }),
      });

      if (!res.ok) {
        throw new Error(`Backend API error: ${res.status} ${res.statusText}`);
      }

      return res.json();
    });

    return this.createSuccessResult(response.data, {
      source: 'backend-proxy',
      cached: response.cached || false,
    });
  }

  private getMockNews(query: string, category: string, days: number, limit: number): ToolResult {
    const mockArticles: NewsArticle[] = [
      {
        title: 'Major Cloud Providers Announce Carbon Neutral Commitments for 2030',
        description: 'Leading cloud computing companies have pledged to achieve carbon neutrality across their global operations by 2030, with significant investments in renewable energy and carbon offset programs.',
        url: 'https://example.com/cloud-carbon-neutral-2030',
        source: 'Tech Climate News',
        publishedAt: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString(),
        relevanceScore: 0.95,
      },
      {
        title: 'New Study Reveals Regional Variations in Data Center Carbon Intensity',
        description: 'Research shows significant differences in carbon emissions per compute unit across global regions, with Nordic countries showing 80% lower emissions than coal-dependent regions.',
        url: 'https://example.com/datacenter-regional-carbon-study',
        source: 'Environmental Computing Journal',
        publishedAt: new Date(Date.now() - 4 * 24 * 60 * 60 * 1000).toISOString(),
        relevanceScore: 0.92,
      },
      {
        title: 'EU Introduces Mandatory Carbon Reporting for Digital Services',
        description: 'New regulations require all digital service providers in the EU to report their carbon footprint and implement reduction strategies by 2025.',
        url: 'https://example.com/eu-digital-carbon-reporting',
        source: 'EU Policy Watch',
        publishedAt: new Date(Date.now() - 1 * 24 * 60 * 60 * 1000).toISOString(),
        relevanceScore: 0.88,
      },
      {
        title: 'Breakthrough in Green Hydrogen Production Could Transform Energy Storage',
        description: 'Scientists develop new catalyst that reduces energy requirements for hydrogen production by 40%, potentially revolutionizing renewable energy storage.',
        url: 'https://example.com/green-hydrogen-breakthrough',
        source: 'Renewable Energy Today',
        publishedAt: new Date(Date.now() - 3 * 24 * 60 * 60 * 1000).toISOString(),
        relevanceScore: 0.85,
      },
      {
        title: 'Carbon Pricing Mechanisms Show Effectiveness in Reducing Industrial Emissions',
        description: 'Analysis of global carbon pricing systems demonstrates average 15% reduction in industrial emissions where implemented.',
        url: 'https://example.com/carbon-pricing-effectiveness',
        source: 'Climate Policy Review',
        publishedAt: new Date(Date.now() - 5 * 24 * 60 * 60 * 1000).toISOString(),
        relevanceScore: 0.82,
      },
    ];

    // Filter articles based on query and category
    let filteredArticles = mockArticles.filter(article => {
      const queryMatch = article.title.toLowerCase().includes(query.toLowerCase()) ||
                         article.description.toLowerCase().includes(query.toLowerCase());
      
      const categoryMatch = !category || 
                            article.title.toLowerCase().includes(category.toLowerCase()) ||
                            article.description.toLowerCase().includes(category.toLowerCase());
      
      const dateMatch = new Date(article.publishedAt) >= new Date(Date.now() - days * 24 * 60 * 60 * 1000);
      
      return queryMatch && categoryMatch && dateMatch;
    });

    // Sort by relevance score and limit results
    filteredArticles = filteredArticles
      .sort((a, b) => (b.relevanceScore || 0) - (a.relevanceScore || 0))
      .slice(0, limit);

    return this.createSuccessResult({
      articles: filteredArticles,
      query,
      category,
      totalResults: filteredArticles.length,
      searchParameters: { query, category, days, limit },
    }, {
      source: 'mock',
      cached: false,
      resultsFound: filteredArticles.length,
    });
  }
}
