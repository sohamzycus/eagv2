/**
 * CarbonLens popup interface
 */

import type { TaskRequest, StreamDelta, TaskResult } from '@/shared/types';
import { generateId } from '@/shared/utils';

interface PopupState {
  currentTaskId?: string;
  isRunning: boolean;
  config: {
    useBackend: boolean;
    samples: number;
  };
}

class CarbonLensPopup {
  private state: PopupState = {
    isRunning: false,
    config: {
      useBackend: false,
      samples: 1000,
    },
  };

  private elements = {
    taskInput: document.getElementById('taskInput') as HTMLTextAreaElement,
    runTaskBtn: document.getElementById('runTaskBtn') as HTMLButtonElement,
    cancelTaskBtn: document.getElementById('cancelTaskBtn') as HTMLButtonElement,
    statusIndicator: document.getElementById('statusIndicator') as HTMLElement,
    statusText: document.getElementById('statusText') as HTMLElement,
    taskStatus: document.getElementById('taskStatus') as HTMLElement,
    progressFill: document.getElementById('progressFill') as HTMLElement,
    progressText: document.getElementById('progressText') as HTMLElement,
    resultsContainer: document.getElementById('resultsContainer') as HTMLElement,
    resultsContent: document.getElementById('resultsContent') as HTMLElement,
    settingsBtn: document.getElementById('settingsBtn') as HTMLButtonElement,
    exportBtn: document.getElementById('exportBtn') as HTMLButtonElement,
    closeResultsBtn: document.getElementById('closeResultsBtn') as HTMLButtonElement,
    openOverlayBtn: document.getElementById('openOverlayBtn') as HTMLButtonElement,
    viewHistoryBtn: document.getElementById('viewHistoryBtn') as HTMLButtonElement,
    useMonteCarlo: document.getElementById('useMonteCarlo') as HTMLInputElement,
    sampleSize: document.getElementById('sampleSize') as HTMLInputElement,
    useBackend: document.getElementById('useBackend') as HTMLInputElement,
  };

  constructor() {
    this.init();
  }

  private async init(): Promise<void> {
    this.setupEventListeners();
    this.setupSamplePrompts();
    await this.loadConfig();
    this.updateUI();
  }

  private setupEventListeners(): void {
    // Main task execution
    this.elements.runTaskBtn.addEventListener('click', () => this.runTask());
    this.elements.cancelTaskBtn.addEventListener('click', () => this.cancelTask());

    // Settings and actions
    this.elements.settingsBtn.addEventListener('click', () => this.openSettings());
    this.elements.exportBtn.addEventListener('click', () => this.exportLogs());
    this.elements.closeResultsBtn.addEventListener('click', () => this.closeResults());
    this.elements.openOverlayBtn.addEventListener('click', () => this.openOverlay());
    this.elements.viewHistoryBtn.addEventListener('click', () => this.viewHistory());

    // Configuration changes
    this.elements.useBackend.addEventListener('change', () => this.updateConfig());
    this.elements.sampleSize.addEventListener('change', () => this.updateConfig());

    // Input handling
    this.elements.taskInput.addEventListener('input', () => this.validateInput());
    this.elements.taskInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
        e.preventDefault();
        this.runTask();
      }
    });
  }

  private setupSamplePrompts(): void {
    const promptButtons = document.querySelectorAll('.prompt-btn');
    promptButtons.forEach(btn => {
      btn.addEventListener('click', () => {
        const prompt = btn.getAttribute('data-prompt');
        if (prompt) {
          this.elements.taskInput.value = prompt;
          this.validateInput();
        }
      });
    });
  }

  private async loadConfig(): Promise<void> {
    try {
      const response = await chrome.runtime.sendMessage({ action: 'getConfig' });
      if (response.success) {
        this.state.config.useBackend = response.config.useRealMode && !!response.config.backendUrl;
        this.elements.useBackend.checked = this.state.config.useBackend;
      }
    } catch (error) {
      console.error('Failed to load config:', error);
    }
  }

  private updateConfig(): void {
    this.state.config.useBackend = this.elements.useBackend.checked;
    this.state.config.samples = parseInt(this.elements.sampleSize.value) || 1000;
  }

  private validateInput(): void {
    const hasInput = this.elements.taskInput.value.trim().length > 0;
    this.elements.runTaskBtn.disabled = !hasInput || this.state.isRunning;
  }

  private async runTask(): Promise<void> {
    const prompt = this.elements.taskInput.value.trim();
    if (!prompt || this.state.isRunning) return;

    this.state.isRunning = true;
    this.updateUI();

    const taskRequest: TaskRequest = {
      prompt,
      samples: this.elements.useMonteCarlo.checked ? this.state.config.samples : undefined,
      useBackend: this.state.config.useBackend,
    };

    try {
      // Start streaming task
      const port = chrome.runtime.connect({ name: 'carbonlens-stream' });
      
      port.postMessage({
        action: 'startStreamingTask',
        taskRequest,
      });

      port.onMessage.addListener((message) => {
        if (message.type === 'started') {
          this.state.currentTaskId = message.taskId;
        } else if (message.type === 'delta') {
          this.handleStreamDelta(message.delta);
        } else if (message.type === 'error') {
          this.handleError(message.error);
        }
      });

      port.onDisconnect.addListener(() => {
        if (this.state.isRunning) {
          this.handleError('Connection lost');
        }
      });

    } catch (error) {
      this.handleError((error as Error).message);
    }
  }

  private handleStreamDelta(delta: StreamDelta): void {
    switch (delta.type) {
      case 'plan':
        this.updateProgress(delta.content, 25);
        break;
      case 'tool_call':
        this.updateProgress(delta.content, 50);
        break;
      case 'tool_result':
        this.updateProgress(delta.content, 75);
        break;
      case 'final':
        this.handleTaskComplete(delta.data);
        break;
      case 'error':
        this.handleError(delta.content);
        break;
    }
  }

  private updateProgress(text: string, percentage: number): void {
    this.elements.progressText.textContent = text;
    this.elements.progressFill.style.width = `${percentage}%`;
  }

  private async handleTaskComplete(result: TaskResult): Promise<void> {
    this.state.isRunning = false;
    this.updateProgress('Task completed', 100);
    
    setTimeout(() => {
      this.showResults(result);
      this.updateUI();
    }, 500);
  }

  private handleError(error: string): void {
    this.state.isRunning = false;
    this.updateStatus('error', `Error: ${error}`);
    this.updateUI();
  }

  private showResults(result: TaskResult): void {
    this.elements.resultsContent.innerHTML = this.formatResult(result);
    this.elements.resultsContainer.style.display = 'block';
    this.elements.taskStatus.style.display = 'none';
  }

  private formatResult(result: TaskResult): string {
    if (!result.success) {
      return `<div class="error">Task failed: ${result.error}</div>`;
    }

    const response = result.result?.response || 'No response available';
    
    return `
      <div class="result-content">
        <div class="result-text">${this.formatMarkdown(response)}</div>
        <div class="result-metadata">
          <div class="metadata-item">
            <span class="label">Steps:</span>
            <span class="value">${result.metadata.totalSteps}</span>
          </div>
          <div class="metadata-item">
            <span class="label">LLM Calls:</span>
            <span class="value">${result.metadata.llmCalls}</span>
          </div>
          <div class="metadata-item">
            <span class="label">Tool Calls:</span>
            <span class="value">${result.metadata.toolCalls}</span>
          </div>
          <div class="metadata-item">
            <span class="label">Duration:</span>
            <span class="value">${((result.metadata.endTime - result.metadata.startTime) / 1000).toFixed(1)}s</span>
          </div>
        </div>
      </div>
    `;
  }

  private formatMarkdown(text: string): string {
    return text
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.*?)\*/g, '<em>$1</em>')
      .replace(/^# (.*$)/gm, '<h1>$1</h1>')
      .replace(/^## (.*$)/gm, '<h2>$1</h2>')
      .replace(/^### (.*$)/gm, '<h3>$1</h3>')
      .replace(/^- (.*$)/gm, '<li>$1</li>')
      .replace(/(<li>.*<\/li>)/gs, '<ul>$1</ul>')
      .replace(/\n\n/g, '</p><p>')
      .replace(/^(.+)$/gm, '<p>$1</p>')
      .replace(/<p><\/p>/g, '');
  }

  private async cancelTask(): Promise<void> {
    if (this.state.currentTaskId) {
      try {
        await chrome.runtime.sendMessage({
          action: 'cancelTask',
          taskId: this.state.currentTaskId,
        });
      } catch (error) {
        console.error('Failed to cancel task:', error);
      }
    }
    
    this.state.isRunning = false;
    this.state.currentTaskId = undefined;
    this.updateUI();
  }

  private closeResults(): void {
    this.elements.resultsContainer.style.display = 'none';
  }

  private async exportLogs(): Promise<void> {
    if (!this.state.currentTaskId) return;

    try {
      const response = await chrome.runtime.sendMessage({
        action: 'exportTaskLogs',
        taskId: this.state.currentTaskId,
      });

      if (response.success) {
        const blob = new Blob([response.logs], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `carbonlens-task-${this.state.currentTaskId}.txt`;
        a.click();
        URL.revokeObjectURL(url);
      }
    } catch (error) {
      console.error('Failed to export logs:', error);
    }
  }

  private openSettings(): void {
    chrome.runtime.openOptionsPage();
  }

  private async openOverlay(): Promise<void> {
    try {
      const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
      if (tab && tab.id) {
        await chrome.scripting.executeScript({
          target: { tabId: tab.id },
          func: () => {
            // Inject overlay iframe
            if (document.getElementById('carbonlens-overlay')) return;
            
            const overlay = document.createElement('iframe');
            overlay.id = 'carbonlens-overlay';
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
          },
        });
      }
    } catch (error) {
      console.error('Failed to open overlay:', error);
    }
  }

  private viewHistory(): void {
    // TODO: Implement history view
    console.log('View history - to be implemented');
  }

  private updateStatus(type: 'ready' | 'running' | 'error', text: string): void {
    this.elements.statusIndicator.className = `status-indicator ${type}`;
    this.elements.statusText.textContent = text;
  }

  private updateUI(): void {
    // Update status
    if (this.state.isRunning) {
      this.updateStatus('running', 'Running analysis...');
      this.elements.taskStatus.style.display = 'block';
    } else {
      this.updateStatus('ready', 'Ready');
      this.elements.taskStatus.style.display = 'none';
    }

    // Update buttons
    this.validateInput();
    this.elements.cancelTaskBtn.disabled = !this.state.isRunning;
    this.elements.exportBtn.disabled = !this.state.currentTaskId;
  }
}

// Initialize popup when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
  new CarbonLensPopup();
});
