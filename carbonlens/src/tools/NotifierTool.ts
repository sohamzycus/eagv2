/**
 * Notifier tool for sending notifications via various channels
 */

import { BaseToolAdapter } from './ToolAdapter';
import type { ToolResult, NotificationChannel } from '@/shared/types';
import { retryWithBackoff } from '@/shared/utils';

export class NotifierTool extends BaseToolAdapter {
  public readonly name = 'NotifierTool';
  public readonly description = 'Send notifications via configured channels (Slack, Telegram, Email)';
  public readonly schema = {
    type: 'object',
    properties: {
      message: {
        type: 'string',
        description: 'Notification message content',
      },
      title: {
        type: 'string',
        description: 'Notification title/subject',
      },
      channel: {
        type: 'string',
        description: 'Notification channel name or type',
      },
      priority: {
        type: 'string',
        description: 'Notification priority level',
        enum: ['low', 'normal', 'high', 'urgent'],
        default: 'normal',
      },
      data: {
        type: 'object',
        description: 'Additional structured data to include',
      },
    },
    required: ['message'],
  };

  constructor(
    private backendUrl?: string,
    private channels: NotificationChannel[] = [],
    private useMock: boolean = true
  ) {
    super();
  }

  public async execute(args: Record<string, any>): Promise<ToolResult> {
    if (!this.validateArgs(args)) {
      return this.createErrorResult('Invalid arguments provided');
    }

    const { message, title, channel, priority = 'normal', data } = args;

    try {
      if (this.useMock) {
        return this.getMockNotification(message, title, channel, priority, data);
      }

      if (this.backendUrl) {
        return await this.sendViaBackend(message, title, channel, priority, data);
      } else {
        return this.createErrorResult('No backend URL configured for notifications');
      }
    } catch (error) {
      return this.createErrorResult(`Notification failed: ${(error as Error).message}`);
    }
  }

  private async sendViaBackend(
    message: string,
    title: string,
    channel: string,
    priority: string,
    data: any
  ): Promise<ToolResult> {
    const payload = {
      message,
      title,
      channel,
      priority,
      data,
      timestamp: new Date().toISOString(),
    };

    const response = await retryWithBackoff(async () => {
      const res = await fetch(`${this.backendUrl}/api/notify`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        throw new Error(`Backend API error: ${res.status} ${res.statusText}`);
      }

      return res.json();
    });

    return this.createSuccessResult(response.data, {
      source: 'backend-proxy',
      deliveryStatus: response.status || 'sent',
    });
  }

  private getMockNotification(
    message: string,
    title: string,
    channel: string,
    priority: string,
    data: any
  ): ToolResult {
    // Simulate different notification channels
    const channelTypes = ['slack', 'telegram', 'email', 'webhook'];
    const selectedChannel = channel || 'default';
    
    // Mock delivery simulation
    const deliverySuccess = Math.random() > 0.05; // 95% success rate
    const deliveryTime = Math.floor(Math.random() * 2000) + 500; // 500-2500ms
    
    if (!deliverySuccess) {
      return this.createErrorResult('Mock notification delivery failed (simulated network error)');
    }

    const notification = {
      id: `notif_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      message,
      title: title || 'CarbonLens Notification',
      channel: selectedChannel,
      priority,
      data,
      timestamp: new Date().toISOString(),
      deliveryTime,
      status: 'delivered',
    };

    // Format message based on channel type
    let formattedMessage = message;
    if (selectedChannel.includes('slack')) {
      formattedMessage = this.formatSlackMessage(message, title, data);
    } else if (selectedChannel.includes('telegram')) {
      formattedMessage = this.formatTelegramMessage(message, title, data);
    } else if (selectedChannel.includes('email')) {
      formattedMessage = this.formatEmailMessage(message, title, data);
    }

    return this.createSuccessResult({
      notification,
      formattedMessage,
      deliveryConfirmation: {
        delivered: true,
        deliveryTime,
        channel: selectedChannel,
        messageId: notification.id,
      },
    }, {
      source: 'mock',
      deliveryTime,
      channel: selectedChannel,
    });
  }

  private formatSlackMessage(message: string, title: string, data: any): string {
    const blocks = [
      {
        type: 'header',
        text: {
          type: 'plain_text',
          text: title || 'CarbonLens Alert',
        },
      },
      {
        type: 'section',
        text: {
          type: 'mrkdwn',
          text: message,
        },
      },
    ];

    if (data) {
      blocks.push({
        type: 'section',
        text: {
          type: 'mrkdwn',
          text: `\`\`\`${JSON.stringify(data, null, 2)}\`\`\``,
        },
      });
    }

    return JSON.stringify({ blocks }, null, 2);
  }

  private formatTelegramMessage(message: string, title: string, data: any): string {
    let formatted = `*${title || 'CarbonLens Alert'}*\n\n${message}`;
    
    if (data) {
      formatted += `\n\n\`\`\`json\n${JSON.stringify(data, null, 2)}\n\`\`\``;
    }
    
    return formatted;
  }

  private formatEmailMessage(message: string, title: string, data: any): string {
    let html = `
      <html>
        <body>
          <h2>${title || 'CarbonLens Alert'}</h2>
          <p>${message}</p>
    `;
    
    if (data) {
      html += `
          <h3>Additional Data:</h3>
          <pre>${JSON.stringify(data, null, 2)}</pre>
      `;
    }
    
    html += `
        </body>
      </html>
    `;
    
    return html;
  }
}
