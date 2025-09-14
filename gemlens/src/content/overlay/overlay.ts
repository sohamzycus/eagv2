/**
 * Overlay chat interface for GemLens
 */

interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  timestamp: number;
}

class GeminiOverlay {
  private chatContainer: HTMLElement;
  private chatInput: HTMLTextAreaElement;
  private sendBtn: HTMLButtonElement;
  private port: chrome.runtime.Port | null = null;
  private messages: ChatMessage[] = [];
  private currentStreamingMessage: HTMLElement | null = null;
  private pageContext: any = null;

  constructor() {
    this.chatContainer = document.getElementById('chatContainer')!;
    this.chatInput = document.getElementById('chatInput') as HTMLTextAreaElement;
    this.sendBtn = document.getElementById('sendBtn') as HTMLButtonElement;
    
    this.setupEventListeners();
    this.connectToBackground();
  }

  private setupEventListeners() {
    // Listen for page context from parent
    window.addEventListener('message', (event) => {
      if (event.data.action === 'setPageContext') {
        this.pageContext = event.data.content;
        console.log('Page context received:', this.pageContext);
      }
    });

    // Close overlay
    document.getElementById('closeOverlay')?.addEventListener('click', () => {
      // Remove overlay from parent page
      if (window.parent !== window) {
        window.parent.postMessage({ action: 'closeOverlay' }, '*');
      } else {
        // Direct removal if not in iframe
        const overlay = document.getElementById('gemlens-overlay');
        if (overlay) overlay.remove();
      }
    });

    // Send message on button click
    this.sendBtn.addEventListener('click', () => {
      this.sendMessage();
    });

    // Send message on Enter (Shift+Enter for new line)
    this.chatInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        this.sendMessage();
      }
    });

    // Auto-resize textarea
    this.chatInput.addEventListener('input', () => {
      this.chatInput.style.height = 'auto';
      this.chatInput.style.height = Math.min(this.chatInput.scrollHeight, 100) + 'px';
    });
  }

  private connectToBackground() {
    try {
      this.port = chrome.runtime.connect({ name: 'gemini-stream' });
      
      this.port.onMessage.addListener((message) => {
        if (message.type === 'delta') {
          this.appendToStreamingMessage(message.chunk);
        } else if (message.type === 'complete') {
          this.finishStreamingMessage();
        } else if (message.type === 'error') {
          this.showError(message.error);
        }
      });

      this.port.onDisconnect.addListener(() => {
        console.log('Port disconnected, attempting to reconnect...');
        setTimeout(() => this.connectToBackground(), 1000);
      });
    } catch (error) {
      console.error('Failed to connect to background:', error);
      // Fallback to direct messaging
      this.port = null;
    }
  }

  private async sendMessage() {
    const text = this.chatInput.value.trim();
    if (!text) return;

    // Add user message
    this.addMessage('user', text);
    this.chatInput.value = '';
    this.chatInput.style.height = 'auto';

    // Disable input while processing
    this.setInputEnabled(false);

    try {
      // Use page context if available, otherwise get it
      let contextText = '';
      if (this.pageContext) {
        contextText = this.pageContext.text;
      } else {
        const pageContent = await this.getPageContent();
        contextText = pageContent.text;
      }

      const contextualPrompt = `Based on this webpage content: "${contextText.substring(0, 2000)}...", please answer: ${text}`;

      // Start streaming response
      this.startStreamingMessage();
      
      if (this.port) {
        this.port.postMessage({
          action: 'streamSummarize',
          text: contextualPrompt
        });
      } else {
        // Fallback to direct messaging if port failed
        try {
          const response = await chrome.runtime.sendMessage({
            action: 'summarizePage',
            text: contextualPrompt
          });
          
          if (response?.error) {
            throw new Error(response.error);
          }
          
          // Simulate streaming for non-streaming response
          this.simulateStreaming(response.summary || 'No response received');
        } catch (fallbackError) {
          this.showError('Connection failed: ' + (fallbackError as Error).message);
        }
      }
    } catch (error) {
      this.showError('Failed to send message: ' + (error as Error).message);
      this.setInputEnabled(true);
    }
  }

  private async getPageContent(): Promise<any> {
    return new Promise((resolve) => {
      // Send message to content script to get page content
      window.parent.postMessage({ action: 'getPageContent' }, '*');
      
      // Listen for response
      const handleMessage = (event: MessageEvent) => {
        if (event.data.action === 'pageContentResponse') {
          window.removeEventListener('message', handleMessage);
          resolve(event.data.content);
        }
      };
      
      window.addEventListener('message', handleMessage);
      
      // Fallback after timeout
      setTimeout(() => {
        window.removeEventListener('message', handleMessage);
        resolve({ text: 'Page content not available', url: window.location.href });
      }, 1000);
    });
  }

  private addMessage(role: 'user' | 'assistant', content: string) {
    const message: ChatMessage = {
      role,
      content,
      timestamp: Date.now()
    };
    
    this.messages.push(message);
    
    const messageEl = document.createElement('div');
    messageEl.className = `message ${role}`;
    messageEl.textContent = content;
    
    this.chatContainer.appendChild(messageEl);
    this.scrollToBottom();
  }

  private startStreamingMessage() {
    this.currentStreamingMessage = document.createElement('div');
    this.currentStreamingMessage.className = 'message assistant streaming';
    this.chatContainer.appendChild(this.currentStreamingMessage);
    this.scrollToBottom();
  }

  private appendToStreamingMessage(chunk: string) {
    if (this.currentStreamingMessage) {
      this.currentStreamingMessage.textContent += chunk;
      this.scrollToBottom();
    }
  }

  private finishStreamingMessage() {
    if (this.currentStreamingMessage) {
      this.currentStreamingMessage.classList.remove('streaming');
      
      const content = this.currentStreamingMessage.textContent || '';
      this.messages.push({
        role: 'assistant',
        content,
        timestamp: Date.now()
      });
      
      this.currentStreamingMessage = null;
    }
    
    this.setInputEnabled(true);
  }

  private showError(error: string) {
    const errorEl = document.createElement('div');
    errorEl.className = 'message assistant';
    errorEl.textContent = `Sorry, I encountered an error: ${error}`;
    errorEl.style.background = '#FF3B30';
    errorEl.style.color = 'white';
    
    this.chatContainer.appendChild(errorEl);
    this.scrollToBottom();
    
    this.setInputEnabled(true);
  }

  private setInputEnabled(enabled: boolean) {
    this.chatInput.disabled = !enabled;
    this.sendBtn.disabled = !enabled;
  }

  private scrollToBottom() {
    this.chatContainer.scrollTop = this.chatContainer.scrollHeight;
  }

  private async simulateStreaming(text: string) {
    const words = text.split(' ');
    const chunkSize = 3;
    
    for (let i = 0; i < words.length; i += chunkSize) {
      const chunk = words.slice(i, i + chunkSize).join(' ') + ' ';
      this.appendToStreamingMessage(chunk);
      await new Promise(resolve => setTimeout(resolve, 50));
    }
    
    this.finishStreamingMessage();
  }
}

// Initialize overlay when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
  new GeminiOverlay();
});
