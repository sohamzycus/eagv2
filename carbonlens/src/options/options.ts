/**
 * CarbonLens Options Page
 */

import type { ExtensionConfig, NotificationChannel } from '@/shared/types';

interface OptionsState {
  config: ExtensionConfig;
  isDirty: boolean;
}

class CarbonLensOptions {
  private state: OptionsState = {
    config: {
      useRealMode: false,
      notificationChannels: [],
    },
    isDirty: false,
  };

  private elements = {
    mockMode: document.getElementById('mockMode') as HTMLInputElement,
    realMode: document.getElementById('realMode') as HTMLInputElement,
    backendUrl: document.getElementById('backendUrl') as HTMLInputElement,
    geminiKey: document.getElementById('geminiKey') as HTMLInputElement,
    carbonInterfaceKey: document.getElementById('carbonInterfaceKey') as HTMLInputElement,
    climatiqKey: document.getElementById('climatiqKey') as HTMLInputElement,
    electricityMapKey: document.getElementById('electricityMapKey') as HTMLInputElement,
    newsApiKey: document.getElementById('newsApiKey') as HTMLInputElement,
    testBackendBtn: document.getElementById('testBackendBtn') as HTMLButtonElement,
    backendTestResult: document.getElementById('backendTestResult') as HTMLElement,
    saveBtn: document.getElementById('saveBtn') as HTMLButtonElement,
    resetBtn: document.getElementById('resetBtn') as HTMLButtonElement,
    exportConfigBtn: document.getElementById('exportConfigBtn') as HTMLButtonElement,
    statusMessage: document.getElementById('statusMessage') as HTMLElement,
    backendSection: document.getElementById('backendSection') as HTMLElement,
    apiKeysSection: document.getElementById('apiKeysSection') as HTMLElement,
    notificationChannels: document.getElementById('notificationChannels') as HTMLElement,
    addChannelBtn: document.getElementById('addChannelBtn') as HTMLButtonElement,
    addChannelModal: document.getElementById('addChannelModal') as HTMLElement,
    closeModalBtn: document.getElementById('closeModalBtn') as HTMLButtonElement,
    cancelChannelBtn: document.getElementById('cancelChannelBtn') as HTMLButtonElement,
    confirmAddChannelBtn: document.getElementById('confirmAddChannelBtn') as HTMLButtonElement,
    channelType: document.getElementById('channelType') as HTMLSelectElement,
    channelName: document.getElementById('channelName') as HTMLInputElement,
    channelEndpoint: document.getElementById('channelEndpoint') as HTMLInputElement,
  };

  constructor() {
    this.init();
  }

  private async init(): Promise<void> {
    await this.loadConfig();
    this.setupEventListeners();
    this.updateUI();
  }

  private async loadConfig(): Promise<void> {
    try {
      const response = await chrome.runtime.sendMessage({ action: 'getConfig' });
      if (response.success) {
        this.state.config = { ...this.state.config, ...response.config };
      }
    } catch (error) {
      console.error('Failed to load config:', error);
    }
  }

  private setupEventListeners(): void {
    // Mode selection
    this.elements.mockMode.addEventListener('change', () => this.onModeChange());
    this.elements.realMode.addEventListener('change', () => this.onModeChange());

    // Input changes
    const inputs = [
      this.elements.backendUrl,
      this.elements.geminiKey,
      this.elements.carbonInterfaceKey,
      this.elements.climatiqKey,
      this.elements.electricityMapKey,
      this.elements.newsApiKey,
    ];

    inputs.forEach(input => {
      input.addEventListener('input', () => this.markDirty());
    });

    // Visibility toggles
    document.querySelectorAll('.toggle-visibility').forEach(btn => {
      btn.addEventListener('click', (e) => {
        const target = (e.target as HTMLElement).getAttribute('data-target');
        if (target) {
          const input = document.getElementById(target) as HTMLInputElement;
          if (input.type === 'password') {
            input.type = 'text';
            (e.target as HTMLElement).textContent = '🙈';
          } else {
            input.type = 'password';
            (e.target as HTMLElement).textContent = '👁️';
          }
        }
      });
    });

    // Actions
    this.elements.testBackendBtn.addEventListener('click', () => this.testBackend());
    this.elements.saveBtn.addEventListener('click', () => this.saveConfig());
    this.elements.resetBtn.addEventListener('click', () => this.resetConfig());
    this.elements.exportConfigBtn.addEventListener('click', () => this.exportConfig());

    // Notification channels
    this.elements.addChannelBtn.addEventListener('click', () => this.openAddChannelModal());
    this.elements.closeModalBtn.addEventListener('click', () => this.closeAddChannelModal());
    this.elements.cancelChannelBtn.addEventListener('click', () => this.closeAddChannelModal());
    this.elements.confirmAddChannelBtn.addEventListener('click', () => this.addNotificationChannel());

    // Modal backdrop click
    this.elements.addChannelModal.addEventListener('click', (e) => {
      if (e.target === this.elements.addChannelModal) {
        this.closeAddChannelModal();
      }
    });
  }

  private onModeChange(): void {
    this.state.config.useRealMode = this.elements.realMode.checked;
    this.markDirty();
    this.updateUI();
  }

  private markDirty(): void {
    this.state.isDirty = true;
    this.elements.saveBtn.textContent = 'Save Settings *';
    this.elements.saveBtn.style.background = 'linear-gradient(135deg, #ed8936 0%, #dd6b20 100%)';
  }

  private updateUI(): void {
    // Update mode selection
    this.elements.mockMode.checked = !this.state.config.useRealMode;
    this.elements.realMode.checked = this.state.config.useRealMode;

    // Show/hide sections based on mode
    if (this.state.config.useRealMode) {
      this.elements.backendSection.classList.remove('hidden');
      this.elements.apiKeysSection.classList.remove('hidden');
    } else {
      this.elements.backendSection.classList.add('hidden');
      this.elements.apiKeysSection.classList.add('hidden');
    }

    // Update form values
    this.elements.backendUrl.value = this.state.config.backendUrl || '';
    this.elements.geminiKey.value = this.state.config.apiKeys?.gemini || '';
    this.elements.carbonInterfaceKey.value = this.state.config.apiKeys?.carbonInterface || '';
    this.elements.climatiqKey.value = this.state.config.apiKeys?.climatiq || '';
    this.elements.electricityMapKey.value = this.state.config.apiKeys?.electricityMap || '';
    this.elements.newsApiKey.value = this.state.config.apiKeys?.newsApi || '';

    // Update notification channels
    this.renderNotificationChannels();
  }

  private renderNotificationChannels(): void {
    const channels = this.state.config.notificationChannels || [];
    
    if (channels.length === 0) {
      this.elements.notificationChannels.innerHTML = `
        <div class="empty-state">
          <span class="icon">📢</span>
          <p>No notification channels configured</p>
          <button class="add-btn" id="addChannelBtn">Add Channel</button>
        </div>
      `;
      
      // Re-attach event listener
      document.getElementById('addChannelBtn')?.addEventListener('click', () => this.openAddChannelModal());
    } else {
      this.elements.notificationChannels.innerHTML = channels.map((channel, index) => `
        <div class="channel-item">
          <div class="channel-info">
            <span class="channel-type">${channel.type}</span>
            <span class="channel-name">${channel.name || 'Unnamed'}</span>
            <small>${channel.endpoint}</small>
          </div>
          <button class="remove-channel" data-index="${index}">Remove</button>
        </div>
      `).join('') + `
        <button class="add-btn" id="addChannelBtn">Add Another Channel</button>
      `;

      // Attach event listeners
      document.getElementById('addChannelBtn')?.addEventListener('click', () => this.openAddChannelModal());
      document.querySelectorAll('.remove-channel').forEach(btn => {
        btn.addEventListener('click', (e) => {
          const index = parseInt((e.target as HTMLElement).getAttribute('data-index') || '0');
          this.removeNotificationChannel(index);
        });
      });
    }
  }

  private async testBackend(): Promise<void> {
    const url = this.elements.backendUrl.value.trim();
    if (!url) {
      this.showTestResult('error', 'Please enter a backend URL');
      return;
    }

    this.elements.testBackendBtn.disabled = true;
    this.elements.testBackendBtn.textContent = 'Testing...';

    try {
      const response = await fetch(`${url}/health`, {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' },
      });

      if (response.ok) {
        const data = await response.json();
        this.showTestResult('success', `✅ Connected successfully! Version: ${data.version || 'unknown'}`);
      } else {
        this.showTestResult('error', `❌ Connection failed: ${response.status} ${response.statusText}`);
      }
    } catch (error) {
      this.showTestResult('error', `❌ Connection failed: ${(error as Error).message}`);
    } finally {
      this.elements.testBackendBtn.disabled = false;
      this.elements.testBackendBtn.textContent = 'Test Connection';
    }
  }

  private showTestResult(type: 'success' | 'error', message: string): void {
    this.elements.backendTestResult.className = `test-result ${type}`;
    this.elements.backendTestResult.textContent = message;
    this.elements.backendTestResult.style.display = 'block';

    setTimeout(() => {
      this.elements.backendTestResult.style.display = 'none';
    }, 5000);
  }

  private async saveConfig(): Promise<void> {
    // Collect form data
    const config: ExtensionConfig = {
      useRealMode: this.elements.realMode.checked,
      backendUrl: this.elements.backendUrl.value.trim() || undefined,
      apiKeys: {
        gemini: this.elements.geminiKey.value.trim() || undefined,
        carbonInterface: this.elements.carbonInterfaceKey.value.trim() || undefined,
        climatiq: this.elements.climatiqKey.value.trim() || undefined,
        electricityMap: this.elements.electricityMapKey.value.trim() || undefined,
        newsApi: this.elements.newsApiKey.value.trim() || undefined,
      },
      notificationChannels: this.state.config.notificationChannels,
    };

    // Remove empty API keys
    if (config.apiKeys) {
      Object.keys(config.apiKeys).forEach(key => {
        if (!config.apiKeys![key as keyof typeof config.apiKeys]) {
          delete config.apiKeys![key as keyof typeof config.apiKeys];
        }
      });
    }

    try {
      const response = await chrome.runtime.sendMessage({
        action: 'updateConfig',
        config,
      });

      if (response.success) {
        this.state.config = config;
        this.state.isDirty = false;
        this.elements.saveBtn.textContent = 'Save Settings';
        this.elements.saveBtn.style.background = 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)';
        this.showStatus('success', '✅ Settings saved successfully!');
      } else {
        this.showStatus('error', '❌ Failed to save settings');
      }
    } catch (error) {
      this.showStatus('error', `❌ Error: ${(error as Error).message}`);
    }
  }

  private async resetConfig(): Promise<void> {
    if (!confirm('Are you sure you want to reset all settings to defaults?')) {
      return;
    }

    const defaultConfig: ExtensionConfig = {
      useRealMode: false,
      notificationChannels: [],
    };

    try {
      const response = await chrome.runtime.sendMessage({
        action: 'updateConfig',
        config: defaultConfig,
      });

      if (response.success) {
        this.state.config = defaultConfig;
        this.state.isDirty = false;
        this.updateUI();
        this.showStatus('success', '✅ Settings reset to defaults');
      }
    } catch (error) {
      this.showStatus('error', `❌ Error: ${(error as Error).message}`);
    }
  }

  private exportConfig(): void {
    const configToExport = {
      ...this.state.config,
      apiKeys: this.state.config.apiKeys ? 
        Object.fromEntries(
          Object.entries(this.state.config.apiKeys).map(([key, value]) => 
            [key, value ? '[REDACTED]' : undefined]
          )
        ) : undefined,
    };

    const blob = new Blob([JSON.stringify(configToExport, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'carbonlens-config.json';
    a.click();
    URL.revokeObjectURL(url);

    this.showStatus('success', '✅ Configuration exported (API keys redacted)');
  }

  private openAddChannelModal(): void {
    this.elements.addChannelModal.style.display = 'flex';
    this.elements.channelName.value = '';
    this.elements.channelEndpoint.value = '';
    this.elements.channelType.value = 'slack';
  }

  private closeAddChannelModal(): void {
    this.elements.addChannelModal.style.display = 'none';
  }

  private addNotificationChannel(): void {
    const type = this.elements.channelType.value as NotificationChannel['type'];
    const name = this.elements.channelName.value.trim();
    const endpoint = this.elements.channelEndpoint.value.trim();

    if (!name || !endpoint) {
      alert('Please fill in all fields');
      return;
    }

    const channel: NotificationChannel = { type, name, endpoint };
    
    if (!this.state.config.notificationChannels) {
      this.state.config.notificationChannels = [];
    }
    
    this.state.config.notificationChannels.push(channel);
    this.markDirty();
    this.renderNotificationChannels();
    this.closeAddChannelModal();
  }

  private removeNotificationChannel(index: number): void {
    if (this.state.config.notificationChannels) {
      this.state.config.notificationChannels.splice(index, 1);
      this.markDirty();
      this.renderNotificationChannels();
    }
  }

  private showStatus(type: 'success' | 'error', message: string): void {
    this.elements.statusMessage.className = `status-message ${type}`;
    this.elements.statusMessage.textContent = message;
    this.elements.statusMessage.style.display = 'block';

    setTimeout(() => {
      this.elements.statusMessage.style.display = 'none';
    }, 3000);
  }
}

// Initialize options page when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
  new CarbonLensOptions();
});
