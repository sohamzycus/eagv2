/**
 * Base interface and utilities for tool adapters
 */

import type { ToolResult } from '@/shared/types';

/**
 * Base interface for all tool adapters
 */
export interface ToolAdapter {
  /** Tool name identifier */
  readonly name: string;
  
  /** Tool description for LLM */
  readonly description: string;
  
  /** Tool parameter schema */
  readonly schema: Record<string, any>;
  
  /**
   * Execute the tool with given arguments
   * @param args - Tool arguments
   * @returns Promise resolving to tool result
   */
  execute(args: Record<string, any>): Promise<ToolResult>;
  
  /**
   * Validate tool arguments against schema
   * @param args - Arguments to validate
   * @returns True if valid, false otherwise
   */
  validateArgs(args: Record<string, any>): boolean;
}

/**
 * Abstract base class for tool adapters
 */
export abstract class BaseToolAdapter implements ToolAdapter {
  public abstract readonly name: string;
  public abstract readonly description: string;
  public abstract readonly schema: Record<string, any>;

  /**
   * Execute the tool - must be implemented by subclasses
   */
  public abstract execute(args: Record<string, any>): Promise<ToolResult>;

  /**
   * Basic argument validation against schema
   */
  public validateArgs(args: Record<string, any>): boolean {
    const required = this.schema.required || [];
    
    // Check required fields
    for (const field of required) {
      if (!(field in args) || args[field] === undefined || args[field] === null) {
        return false;
      }
    }
    
    // Check field types if specified
    const properties = this.schema.properties || {};
    for (const [key, value] of Object.entries(args)) {
      const propSchema = properties[key];
      if (propSchema && propSchema.type) {
        const actualType = typeof value;
        const expectedType = propSchema.type;
        
        if (expectedType === 'integer' && !Number.isInteger(value)) {
          return false;
        } else if (expectedType === 'number' && typeof value !== 'number') {
          return false;
        } else if (expectedType === 'string' && typeof value !== 'string') {
          return false;
        } else if (expectedType === 'boolean' && typeof value !== 'boolean') {
          return false;
        } else if (expectedType === 'array' && !Array.isArray(value)) {
          return false;
        } else if (expectedType === 'object' && (typeof value !== 'object' || Array.isArray(value))) {
          return false;
        }
      }
    }
    
    return true;
  }

  /**
   * Create a successful tool result
   */
  protected createSuccessResult(data: any, metadata?: any): ToolResult {
    return {
      success: true,
      data,
      metadata: {
        executionTime: Date.now(),
        source: this.name,
        ...metadata,
      },
    };
  }

  /**
   * Create an error tool result
   */
  protected createErrorResult(error: string, metadata?: any): ToolResult {
    return {
      success: false,
      error,
      metadata: {
        executionTime: Date.now(),
        source: this.name,
        ...metadata,
      },
    };
  }
}

/**
 * Tool registry for managing available tools
 */
export class ToolRegistry {
  private tools = new Map<string, ToolAdapter>();

  /**
   * Register a tool adapter
   */
  public register(tool: ToolAdapter): void {
    this.tools.set(tool.name, tool);
  }

  /**
   * Get a tool by name
   */
  public get(name: string): ToolAdapter | undefined {
    return this.tools.get(name);
  }

  /**
   * Get all registered tools
   */
  public getAll(): ToolAdapter[] {
    return Array.from(this.tools.values());
  }

  /**
   * Check if a tool is registered
   */
  public has(name: string): boolean {
    return this.tools.has(name);
  }

  /**
   * Execute a tool by name
   */
  public async execute(name: string, args: Record<string, any>): Promise<ToolResult> {
    const tool = this.get(name);
    if (!tool) {
      return {
        success: false,
        error: `Tool '${name}' not found`,
        metadata: {
          executionTime: Date.now(),
          source: 'ToolRegistry',
        },
      };
    }

    if (!tool.validateArgs(args)) {
      return {
        success: false,
        error: `Invalid arguments for tool '${name}'`,
        metadata: {
          executionTime: Date.now(),
          source: 'ToolRegistry',
        },
      };
    }

    try {
      return await tool.execute(args);
    } catch (error) {
      return {
        success: false,
        error: `Tool execution failed: ${(error as Error).message}`,
        metadata: {
          executionTime: Date.now(),
          source: 'ToolRegistry',
        },
      };
    }
  }
}
