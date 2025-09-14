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
  private historyContainer: HTMLElement;
  private historyContent: HTMLElement;

  constructor() {
    this.statusIndicator = document.getElementById('statusIndicator')!;
    this.statusText = document.getElementById('statusText')!;
    this.summaryContainer = document.getElementById('summaryContainer')!;
    this.summaryContent = document.getElementById('summaryContent')!;
    this.historyContainer = document.getElementById('historyContainer')!;
    this.historyContent = document.getElementById('historyContent')!;

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

    // History
    document.getElementById('historyBtn')?.addEventListener('click', () => {
      this.showHistory();
    });

    // Close history
    document.getElementById('closeHistory')?.addEventListener('click', () => {
      this.closeHistory();
    });

    // Save summary
    document.getElementById('saveBtn')?.addEventListener('click', () => {
      this.saveSummary();
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
        url: content.url,
        title: content.title || this.currentTab?.title || 'Untitled Page',
        type: content.type || 'webpage'
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

  private async showHistory() {
    try {
      this.historyContainer.style.display = 'block';
      this.historyContent.innerHTML = '<div class="loading">Loading history...</div>';
      
      const response = await chrome.runtime.sendMessage({ action: 'getHistory' });
      
      if (response?.history && response.history.length > 0) {
        this.displayHistory(response.history);
      } else {
        this.historyContent.innerHTML = '<div style="padding: 20px; text-align: center; color: #666;">No summaries yet</div>';
      }
    } catch (error) {
      this.historyContent.innerHTML = '<div style="padding: 20px; text-align: center; color: #ff3b30;">Failed to load history</div>';
    }
  }

  private displayHistory(history: any[]) {
    this.historyContent.innerHTML = '';
    
    history.forEach((item, index) => {
      const historyItem = document.createElement('div');
      historyItem.className = 'history-item';
      
      const date = new Date(item.timestamp).toLocaleDateString();
      const preview = item.summary.substring(0, 100) + (item.summary.length > 100 ? '...' : '');
      
      historyItem.innerHTML = `
        <div class="history-item-title">${item.title}</div>
        <div class="history-item-url">${item.url}</div>
        <div class="history-item-preview">${preview}</div>
        <div class="history-item-date">${date}</div>
      `;
      
      historyItem.addEventListener('click', () => {
        this.showHistoryItem(item);
      });
      
      this.historyContent.appendChild(historyItem);
    });
  }

  private showHistoryItem(item: any) {
    this.summaryContent.textContent = item.summary;
    this.summaryContainer.style.display = 'block';
    this.historyContainer.style.display = 'none';
  }

  private closeHistory() {
    this.historyContainer.style.display = 'none';
  }

  private async saveSummary() {
    // Summary is already saved automatically, just show feedback
    const saveBtn = document.getElementById('saveBtn') as HTMLButtonElement;
    const originalText = saveBtn.textContent;
    saveBtn.textContent = 'Saved!';
    saveBtn.style.background = '#34C759';
    
    setTimeout(() => {
      saveBtn.textContent = originalText;
      saveBtn.style.background = '#34C759';
    }, 1000);
  }
}

// Initialize popup when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
  new GemLensPopup();
});
