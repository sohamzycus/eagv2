/**
 * Popup interface for GemLens extension
 */

interface TabInfo {
  id?: number;
  url?: string;
  title?: string;
}

class GemLensPopup {
  private currentTab: TabInfo | null = null;
  private statusIndicator: HTMLElement;
  private statusText: HTMLElement;
  private summaryContainer: HTMLElement;
  private summaryContent: HTMLElement;

  constructor() {
    this.statusIndicator = document.getElementById('statusIndicator')!;
    this.statusText = document.getElementById('statusText')!;
    this.summaryContainer = document.getElementById('summaryContainer')!;
    this.summaryContent = document.getElementById('summaryContent')!;

    this.init();
  }

  private async init() {
    await this.getCurrentTab();
    await this.checkApiKeyStatus();
    this.setupEventListeners();
  }

  private async getCurrentTab(): Promise<void> {
    try {
      const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
      this.currentTab = tab;
    } catch (error) {
      console.error('Failed to get current tab:', error);
    }
  }

  private async checkApiKeyStatus(): Promise<void> {
    try {
      const response = await chrome.runtime.sendMessage({ action: 'checkApiKey' });
      
      if (response?.hasKey) {
        this.updateStatus('ready', 'Ready to summarize');
        this.enableButtons(true);
      } else {
        this.updateStatus('warning', 'API key required');
        this.enableButtons(false);
      }
    } catch (error) {
      this.updateStatus('error', 'Extension error');
      this.enableButtons(false);
    }
  }

  private updateStatus(type: 'ready' | 'warning' | 'error', message: string) {
    const dot = this.statusIndicator.querySelector('.status-dot') as HTMLElement;
    dot.className = `status-dot ${type === 'ready' ? '' : type}`;
    this.statusText.textContent = message;
  }

  private enableButtons(enabled: boolean) {
    const buttons = document.querySelectorAll('.action-btn') as NodeListOf<HTMLButtonElement>;
    buttons.forEach(btn => {
      btn.disabled = !enabled;
    });
  }

  private setupEventListeners() {
    // Summarize page
    document.getElementById('summarizeBtn')?.addEventListener('click', () => {
      this.summarizePage();
    });

    // Summarize video
    document.getElementById('summarizeVideoBtn')?.addEventListener('click', () => {
      this.summarizeVideo();
    });

    // Ask Gemini (open overlay)
    document.getElementById('askGeminiBtn')?.addEventListener('click', () => {
      this.openGeminiChat();
    });

    // Settings
    document.getElementById('settingsBtn')?.addEventListener('click', () => {
      chrome.runtime.openOptionsPage();
    });

    // Close summary
    document.getElementById('closeSummary')?.addEventListener('click', () => {
      this.closeSummary();
    });

    // Copy summary
    document.getElementById('copyBtn')?.addEventListener('click', () => {
      this.copySummary();
    });
  }

  private async summarizePage() {
    if (!this.currentTab?.id) return;

    try {
      this.showLoading('Extracting page content...');

      // Extract content from current tab
      const [result] = await chrome.scripting.executeScript({
        target: { tabId: this.currentTab.id },
        func: () => {
          // This function runs in the content script context
          return new Promise((resolve) => {
            chrome.runtime.sendMessage({ action: 'extractContent' }, (response) => {
              resolve(response);
            });
          });
        }
      });

      if (!result?.result?.success) {
        throw new Error('Failed to extract page content');
      }

      const content = result.result.content;
      this.showLoading('Generating summary...');

      // Send to background for summarization
      const response = await chrome.runtime.sendMessage({
        action: 'summarizePage',
        text: content.text,
        url: content.url
      });

      if (response?.error) {
        throw new Error(response.error);
      }

      this.showSummary(response.summary);
    } catch (error) {
      this.showError('Failed to summarize page: ' + (error as Error).message);
    }
  }

  private async summarizeVideo() {
    if (!this.currentTab?.id) return;

    try {
      this.showLoading('Extracting video content...');

      // Check if current page is a video platform
      if (!this.currentTab.url?.includes('youtube.com')) {
        throw new Error('Video summarization currently supports YouTube only');
      }

      // Extract video content
      const [result] = await chrome.scripting.executeScript({
        target: { tabId: this.currentTab.id },
        func: () => {
          return new Promise((resolve) => {
            chrome.runtime.sendMessage({ action: 'extractContent' }, (response) => {
              resolve(response);
            });
          });
        }
      });

      if (!result?.result?.success) {
        throw new Error('Failed to extract video content');
      }

      const content = result.result.content;
      if (content.type !== 'video') {
        throw new Error('No video content detected on this page');
      }

      this.showLoading('Generating video summary...');

      // Use video-specific content for summarization
      const textToSummarize = content.captions || content.text;
      const response = await chrome.runtime.sendMessage({
        action: 'summarizePage',
        text: `Video content: ${textToSummarize}`,
        url: content.url
      });

      if (response?.error) {
        throw new Error(response.error);
      }

      this.showSummary(response.summary);
    } catch (error) {
      this.showError('Failed to summarize video: ' + (error as Error).message);
    }
  }

  private async openGeminiChat() {
    if (!this.currentTab?.id) return;

    try {
      // Inject overlay into current tab
      await chrome.scripting.executeScript({
        target: { tabId: this.currentTab.id },
        func: () => {
          chrome.runtime.sendMessage({ action: 'showOverlay' });
        }
      });

      // Close popup
      window.close();
    } catch (error) {
      this.showError('Failed to open chat: ' + (error as Error).message);
    }
  }

  private showLoading(message: string) {
    this.updateStatus('ready', message);
    this.enableButtons(false);
    
    // Add loading animation to active button
    const activeBtn = document.querySelector('.action-btn:not(:disabled)') as HTMLElement;
    if (activeBtn) {
      activeBtn.classList.add('loading');
    }
  }

  private showSummary(summary: string) {
    this.summaryContent.textContent = summary;
    this.summaryContainer.style.display = 'block';
    this.updateStatus('ready', 'Summary generated');
    this.enableButtons(true);
    
    // Remove loading animation
    document.querySelectorAll('.action-btn').forEach(btn => {
      btn.classList.remove('loading');
    });
  }

  private showError(message: string) {
    this.updateStatus('error', message);
    this.enableButtons(true);
    
    // Remove loading animation
    document.querySelectorAll('.action-btn').forEach(btn => {
      btn.classList.remove('loading');
    });
  }

  private closeSummary() {
    this.summaryContainer.style.display = 'none';
  }

  private async copySummary() {
    try {
      await navigator.clipboard.writeText(this.summaryContent.textContent || '');
      
      // Show feedback
      const copyBtn = document.getElementById('copyBtn') as HTMLButtonElement;
      const originalText = copyBtn.textContent;
      copyBtn.textContent = 'Copied!';
      copyBtn.style.background = '#34C759';
      
      setTimeout(() => {
        copyBtn.textContent = originalText;
        copyBtn.style.background = '#007AFF';
      }, 1000);
    } catch (error) {
      console.error('Failed to copy summary:', error);
    }
  }
}

// Initialize popup when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
  new GemLensPopup();
});
