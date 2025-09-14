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
    document.getElementById('summarizePageBtn')?.addEventListener('click', () => {
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

      // Add timeout to prevent hanging
      const timeoutPromise = new Promise((_, reject) => {
        setTimeout(() => reject(new Error('Content extraction timed out after 10 seconds')), 10000);
      });

      // Extract content directly from current tab
      const extractionPromise = chrome.scripting.executeScript({
        target: { tabId: this.currentTab.id },
        func: () => {
          // Direct content extraction function
          const extractPageContent = () => {
            const url = window.location.href;
            const title = document.title;
            
            let text = '';
            
            // Try to find main content areas
            const contentSelectors = [
              'article',
              'main',
              '[role="main"]',
              '.content',
              '#content',
              '.post-content',
              '.entry-content'
            ];
            
            for (const selector of contentSelectors) {
              const element = document.querySelector(selector);
              if (element) {
                text = element.textContent || element.innerText || '';
                break;
              }
            }
            
            // Fallback to body content, but filter out navigation and footer
            if (!text) {
              const body = document.body.cloneNode(true) as HTMLElement;
              
              // Remove common non-content elements
              const removeSelectors = [
                'nav', 'header', 'footer', 'aside',
                '.navigation', '.nav', '.menu',
                '.sidebar', '.footer', '.header'
              ];
              
              removeSelectors.forEach(selector => {
                const elements = body.querySelectorAll(selector);
                elements.forEach(el => el.remove());
              });
              
              text = body.textContent || body.innerText || '';
            }
            
            // Clean up text
            text = text.replace(/\s+/g, ' ').trim();
            
            const result = {
              text,
              title,
              url,
              type: window.location.hostname.includes('youtube.com') ? 'video' : 'webpage'
            };
            
            return result;
          };
          
          return extractPageContent();
        }
      });

      // Race between extraction and timeout
      const [result] = await Promise.race([extractionPromise, timeoutPromise]) as any[];

      if (!result?.result) {
        throw new Error('Failed to extract page content');
      }

      const content = result.result;
      
      // Show extracted content length for debugging
      console.log('Extracted content length:', content.text.length);
      console.log('Extracted content preview:', content.text.substring(0, 200) + '...');
      
      if (!content.text || content.text.length < 50) {
        throw new Error(`Not enough content extracted (${content.text.length} characters). Try refreshing the page.`);
      }
      
      this.showLoading(`Generating summary... (${content.text.length} chars extracted)`);

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

      if (!response?.summary) {
        throw new Error('No summary received from AI service');
      }

      console.log('Summary received:', response.summary.length, 'characters');
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

      // Add timeout to prevent hanging
      const timeoutPromise = new Promise((_, reject) => {
        setTimeout(() => reject(new Error('Video content extraction timed out after 15 seconds')), 15000);
      });

      // Extract video content directly
      const extractionPromise = chrome.scripting.executeScript({
        target: { tabId: this.currentTab.id },
        func: () => {
          const extractVideoContent = () => {
            const url = window.location.href;
            const title = document.title;
            
            // Get video title and description
            let text = '';
            
            // YouTube video title
            const videoTitle = document.querySelector('h1.ytd-video-primary-info-renderer') || 
                              document.querySelector('h1.title') ||
                              document.querySelector('.watch-main-col h1');
            
            if (videoTitle) {
              text += 'Video Title: ' + videoTitle.textContent + '\n\n';
            }
            
            // YouTube video description
            const description = document.querySelector('#description') ||
                               document.querySelector('.watch-main-col .content') ||
                               document.querySelector('ytd-video-secondary-info-renderer');
            
            if (description) {
              text += 'Description: ' + description.textContent + '\n\n';
            }
            
            // Try to get transcript/captions
            const transcriptButton = document.querySelector('[aria-label*="transcript" i], [aria-label*="captions" i]');
            if (transcriptButton) {
              text += 'Transcript available but requires user interaction to access.\n\n';
            }
            
            // Get comments as additional context
            const comments = document.querySelectorAll('#content-text, .comment-text');
            if (comments.length > 0) {
              text += 'Top Comments:\n';
              Array.from(comments).slice(0, 5).forEach((comment, i) => {
                text += `${i + 1}. ${comment.textContent?.trim()}\n`;
              });
            }
            
            // Fallback to page content
            if (!text || text.length < 100) {
              const body = document.body.cloneNode(true) as HTMLElement;
              
              // Remove non-content elements
              const removeSelectors = [
                'nav', 'header', 'footer', 'aside', '.navigation', 
                '.sidebar', '#chat', '.live-chat', 'script', 'style'
              ];
              
              removeSelectors.forEach(selector => {
                const elements = body.querySelectorAll(selector);
                elements.forEach(el => el.remove());
              });
              
              text = body.textContent || body.innerText || '';
            }
            
            // Clean up text
            text = text.replace(/\s+/g, ' ').trim();
            
            return {
              text,
              title,
              url,
              type: 'video'
            };
          };
          
          return extractVideoContent();
        }
      });

      // Race between extraction and timeout
      const [result] = await Promise.race([extractionPromise, timeoutPromise]) as any[];

      if (!result?.result) {
        throw new Error('Failed to extract video content');
      }

      const content = result.result;
      
      console.log('Video content extracted:', content.text.length, 'characters');
      console.log('Video content preview:', content.text.substring(0, 300) + '...');
      
      if (!content.text || content.text.length < 50) {
        throw new Error(`Not enough video content extracted (${content.text.length} characters). Try refreshing the page.`);
      }

      this.showLoading(`Generating video summary... (${content.text.length} chars extracted)`);

      // Send to background for summarization with video-specific prompt
      const response = await chrome.runtime.sendMessage({
        action: 'summarizePage',
        text: `YouTube Video Content:\n${content.text}`,
        url: content.url,
        title: content.title || this.currentTab?.title || 'YouTube Video',
        type: 'video'
      });

      if (response?.error) {
        throw new Error(response.error);
      }

      if (!response?.summary) {
        throw new Error('No video summary received from AI service');
      }

      console.log('Video summary received:', response.summary.length, 'characters');
      this.showSummary(response.summary);
    } catch (error) {
      this.showError('Failed to summarize video: ' + (error as Error).message);
    }
  }

  private async openGeminiChat() {
    if (!this.currentTab?.id) return;

    try {
      this.showLoading('Opening Gemini chat...');

      // Inject the overlay directly
      await chrome.scripting.executeScript({
        target: { tabId: this.currentTab.id },
        func: () => {
          // Check if overlay already exists
          if (document.getElementById('gemlens-overlay')) {
            return;
          }
          
          // Create overlay iframe
          const overlay = document.createElement('iframe');
          overlay.id = 'gemlens-overlay';
          overlay.src = chrome.runtime.getURL('content/overlay/overlay.html');
          overlay.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            width: 400px;
            height: 600px;
            border: none;
            border-radius: 12px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
            z-index: 10000;
            background: white;
          `;
          
          document.body.appendChild(overlay);
          
          // Add close functionality
          overlay.addEventListener('load', () => {
            // Send page content to overlay for context
            const pageContent = {
              title: document.title,
              url: window.location.href,
              text: document.body.textContent?.substring(0, 2000) || ''
            };
            
            overlay.contentWindow?.postMessage({
              action: 'setPageContext',
              content: pageContent
            }, '*');
          });

          // Listen for close message from overlay
          window.addEventListener('message', (event) => {
            if (event.data.action === 'closeOverlay') {
              overlay.remove();
            }
          });
        }
      });

      // Update status
      this.updateStatus('ready', 'Chat opened');
      this.enableButtons(true);
      
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
    
    // Keep popup open longer during processing
    console.log('GemLens:', message);
  }

  private showSummary(summary: string) {
    // Format and display summary with proper HTML rendering
    this.summaryContent.innerHTML = this.formatSummary(summary);
    this.summaryContainer.style.display = 'block';
    this.updateStatus('ready', 'Summary generated');
    this.enableButtons(true);
    
    // Remove loading animation
    document.querySelectorAll('.action-btn').forEach(btn => {
      btn.classList.remove('loading');
    });
  }

  private formatSummary(text: string): string {
    return text
      // Convert **text** to <strong>text</strong>
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      // Convert bullet points
      .replace(/^• (.+)$/gm, '<li>$1</li>')
      // Wrap consecutive li elements in ul
      .replace(/(<li>.*<\/li>)/gs, '<ul>$1</ul>')
      // Convert line breaks to paragraphs
      .split('\n\n')
      .map(paragraph => paragraph.trim() ? `<p>${paragraph.replace(/\n/g, '<br>')}</p>` : '')
      .join('');
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
