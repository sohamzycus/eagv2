/**
 * Options page for GemLens extension
 */

interface UserPreferences {
  autoSummarize: boolean;
  summaryLength: 'short' | 'medium' | 'long';
  language: string;
}

interface UsageStats {
  totalSummaries: number;
  totalChats: number;
  timesSaved: number; // in minutes
}

class GemLensOptions {
  private apiKeyInput: HTMLInputElement;
  private toggleBtn: HTMLButtonElement;
  private saveBtn: HTMLButtonElement;
  private testBtn: HTMLButtonElement;
  private clearBtn: HTMLButtonElement;
  private statusMessage: HTMLElement;
  
  private autoSummarizeCheckbox: HTMLInputElement;
  private summaryLengthSelect: HTMLSelectElement;
  private languageSelect: HTMLSelectElement;
  
  private isApiKeyVisible = false;

  constructor() {
    this.apiKeyInput = document.getElementById('apiKey') as HTMLInputElement;
    this.toggleBtn = document.getElementById('toggleApiKey') as HTMLButtonElement;
    this.saveBtn = document.getElementById('saveBtn') as HTMLButtonElement;
    this.testBtn = document.getElementById('testBtn') as HTMLButtonElement;
    this.clearBtn = document.getElementById('clearBtn') as HTMLButtonElement;
    this.statusMessage = document.getElementById('statusMessage')!;
    
    this.autoSummarizeCheckbox = document.getElementById('autoSummarize') as HTMLInputElement;
    this.summaryLengthSelect = document.getElementById('summaryLength') as HTMLSelectElement;
    this.languageSelect = document.getElementById('language') as HTMLSelectElement;

    this.init();
  }

  private async init() {
    await this.loadSettings();
    await this.loadStats();
    this.setupEventListeners();
  }

  private async loadSettings() {
    try {
      // Load API key status
      const result = await chrome.storage.local.get(['GEMINI_API_KEY']);
      if (result.GEMINI_API_KEY) {
        this.apiKeyInput.value = '••••••••••••••••';
        this.apiKeyInput.dataset.hasKey = 'true';
        this.showStatus('API key is configured', 'success');
      }

      // Load user preferences
      const prefs = await chrome.storage.local.get(['userPreferences']);
      if (prefs.userPreferences) {
        const preferences: UserPreferences = prefs.userPreferences;
        this.autoSummarizeCheckbox.checked = preferences.autoSummarize || false;
        this.summaryLengthSelect.value = preferences.summaryLength || 'medium';
        this.languageSelect.value = preferences.language || 'en';
      }
    } catch (error) {
      console.error('Failed to load settings:', error);
    }
  }

  private async loadStats() {
    try {
      const result = await chrome.storage.local.get(['usageStats']);
      const stats: UsageStats = result.usageStats || {
        totalSummaries: 0,
        totalChats: 0,
        timesSaved: 0
      };

      document.getElementById('totalSummaries')!.textContent = stats.totalSummaries.toString();
      document.getElementById('totalChats')!.textContent = stats.totalChats.toString();
      document.getElementById('timesSaved')!.textContent = `${Math.round(stats.timesSaved / 60)}h`;
    } catch (error) {
      console.error('Failed to load stats:', error);
    }
  }

  private setupEventListeners() {
    // API Key management
    this.toggleBtn.addEventListener('click', () => this.toggleApiKeyVisibility());
    this.saveBtn.addEventListener('click', () => this.saveApiKey());
    this.testBtn.addEventListener('click', () => this.testApiKey());
    this.clearBtn.addEventListener('click', () => this.clearApiKey());

    // Auto-save preferences
    this.autoSummarizeCheckbox.addEventListener('change', () => this.savePreferences());
    this.summaryLengthSelect.addEventListener('change', () => this.savePreferences());
    this.languageSelect.addEventListener('change', () => this.savePreferences());

    // Other buttons
    document.getElementById('resetStatsBtn')?.addEventListener('click', () => this.resetStats());
    document.getElementById('reportIssue')?.addEventListener('click', () => this.reportIssue());
    document.getElementById('showVersion')?.addEventListener('click', () => this.showVersionInfo());

    // Handle Enter key in API key input
    this.apiKeyInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') {
        this.saveApiKey();
      }
    });

    // Clear placeholder when focusing on masked input
    this.apiKeyInput.addEventListener('focus', () => {
      if (this.apiKeyInput.dataset.hasKey === 'true' && !this.isApiKeyVisible) {
        this.apiKeyInput.value = '';
        this.apiKeyInput.placeholder = 'Enter new API key or leave blank to keep current';
      }
    });
  }

  private toggleApiKeyVisibility() {
    this.isApiKeyVisible = !this.isApiKeyVisible;
    
    if (this.isApiKeyVisible) {
      this.apiKeyInput.type = 'text';
      this.toggleBtn.innerHTML = `
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"></path>
          <line x1="1" y1="1" x2="23" y2="23"></line>
        </svg>
      `;
    } else {
      this.apiKeyInput.type = 'password';
      this.toggleBtn.innerHTML = `
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path>
          <circle cx="12" cy="12" r="3"></circle>
        </svg>
      `;
    }
  }

  private async saveApiKey() {
    const apiKey = this.apiKeyInput.value.trim();
    
    if (!apiKey || apiKey === '••••••••••••••••') {
      this.showStatus('Please enter a valid API key', 'error');
      return;
    }

    if (!apiKey.startsWith('AIza')) {
      this.showStatus('Invalid API key format. Google API keys start with "AIza"', 'error');
      return;
    }

    try {
      this.setButtonLoading(this.saveBtn, true);
      
      await chrome.storage.local.set({ GEMINI_API_KEY: apiKey });
      
      // Notify background script to refresh
      await chrome.runtime.sendMessage({ action: 'refreshApiKey' });
      
      this.apiKeyInput.value = '••••••••••••••••';
      this.apiKeyInput.dataset.hasKey = 'true';
      this.showStatus('API key saved successfully!', 'success');
      
    } catch (error) {
      this.showStatus('Failed to save API key: ' + (error as Error).message, 'error');
    } finally {
      this.setButtonLoading(this.saveBtn, false);
    }
  }

  private async testApiKey() {
    try {
      this.setButtonLoading(this.testBtn, true);
      
      const result = await chrome.storage.local.get(['GEMINI_API_KEY']);
      if (!result.GEMINI_API_KEY) {
        this.showStatus('No API key found. Please save an API key first.', 'error');
        return;
      }

      // Test with a simple summarization request
      const response = await chrome.runtime.sendMessage({
        action: 'summarizePage',
        text: 'This is a test message to verify the API key is working correctly.',
        url: 'test'
      });

      if (response?.error) {
        this.showStatus('API key test failed: ' + response.error, 'error');
      } else if (response?.summary) {
        this.showStatus('API key is working correctly! ✅', 'success');
      } else {
        this.showStatus('Unexpected response from API', 'error');
      }
      
    } catch (error) {
      this.showStatus('Failed to test API key: ' + (error as Error).message, 'error');
    } finally {
      this.setButtonLoading(this.testBtn, false);
    }
  }

  private async clearApiKey() {
    if (!confirm('Are you sure you want to clear your API key? You will need to enter it again to use GemLens.')) {
      return;
    }

    try {
      await chrome.storage.local.remove(['GEMINI_API_KEY']);
      await chrome.runtime.sendMessage({ action: 'refreshApiKey' });
      
      this.apiKeyInput.value = '';
      this.apiKeyInput.placeholder = 'Enter your Gemini API key...';
      delete this.apiKeyInput.dataset.hasKey;
      
      this.showStatus('API key cleared', 'info');
    } catch (error) {
      this.showStatus('Failed to clear API key: ' + (error as Error).message, 'error');
    }
  }

  private async savePreferences() {
    const preferences: UserPreferences = {
      autoSummarize: this.autoSummarizeCheckbox.checked,
      summaryLength: this.summaryLengthSelect.value as 'short' | 'medium' | 'long',
      language: this.languageSelect.value
    };

    try {
      await chrome.storage.local.set({ userPreferences: preferences });
      this.showStatus('Preferences saved', 'success', 2000);
    } catch (error) {
      this.showStatus('Failed to save preferences: ' + (error as Error).message, 'error');
    }
  }

  private async resetStats() {
    if (!confirm('Are you sure you want to reset all usage statistics?')) {
      return;
    }

    try {
      const resetStats: UsageStats = {
        totalSummaries: 0,
        totalChats: 0,
        timesSaved: 0
      };

      await chrome.storage.local.set({ usageStats: resetStats });
      await this.loadStats();
      
      this.showStatus('Statistics reset successfully', 'success');
    } catch (error) {
      this.showStatus('Failed to reset statistics: ' + (error as Error).message, 'error');
    }
  }

  private reportIssue() {
    const issueUrl = 'https://github.com/your-username/gemlens/issues/new';
    window.open(issueUrl, '_blank');
  }

  private showVersionInfo() {
    const manifest = chrome.runtime.getManifest();
    alert(`GemLens v${manifest.version}\n\nA Chrome extension for AI-powered webpage and video summarization using Google Gemini.`);
  }

  private showStatus(message: string, type: 'success' | 'error' | 'info', duration = 5000) {
    this.statusMessage.textContent = message;
    this.statusMessage.className = `status-message ${type}`;
    this.statusMessage.style.display = 'block';

    setTimeout(() => {
      this.statusMessage.style.display = 'none';
    }, duration);
  }

  private setButtonLoading(button: HTMLButtonElement, loading: boolean) {
    if (loading) {
      button.disabled = true;
      button.style.opacity = '0.7';
      button.textContent = 'Loading...';
    } else {
      button.disabled = false;
      button.style.opacity = '1';
      
      // Restore original text based on button ID
      if (button === this.saveBtn) button.textContent = 'Save API Key';
      else if (button === this.testBtn) button.textContent = 'Test Connection';
    }
  }
}

// Initialize options page when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
  new GemLensOptions();
});
