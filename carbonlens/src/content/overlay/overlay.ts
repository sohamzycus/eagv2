/**
 * CarbonLens overlay for agent trace visualization
 */

import type { StreamDelta } from '@/shared/types';

interface TraceStep {
  id: string;
  type: 'plan' | 'tool_call' | 'tool_result' | 'final' | 'error';
  title: string;
  content: any;
  timestamp: number;
  expanded: boolean;
}

class CarbonLensOverlay {
  private steps: TraceStep[] = [];
  private autoScroll = true;
  private currentTaskId?: string;

  private elements = {
    traceStatus: document.getElementById('traceStatus') as HTMLElement,
    welcomeState: document.getElementById('welcomeState') as HTMLElement,
    traceSteps: document.getElementById('traceSteps') as HTMLElement,
    traceContainer: document.getElementById('traceContainer') as HTMLElement,
    closeOverlay: document.getElementById('closeOverlay') as HTMLButtonElement,
    clearTraceBtn: document.getElementById('clearTraceBtn') as HTMLButtonElement,
    exportTraceBtn: document.getElementById('exportTraceBtn') as HTMLButtonElement,
    toggleAutoScrollBtn: document.getElementById('toggleAutoScrollBtn') as HTMLButtonElement,
  };

  constructor() {
    this.init();
  }

  private init(): void {
    this.setupEventListeners();
    this.connectToBackground();
    this.updateStatus('Ready');
  }

  private setupEventListeners(): void {
    // Close overlay
    this.elements.closeOverlay.addEventListener('click', () => {
      this.closeOverlay();
    });

    // Clear trace
    this.elements.clearTraceBtn.addEventListener('click', () => {
      this.clearTrace();
    });

    // Export trace
    this.elements.exportTraceBtn.addEventListener('click', () => {
      this.exportTrace();
    });

    // Toggle auto-scroll
    this.elements.toggleAutoScrollBtn.addEventListener('click', () => {
      this.toggleAutoScroll();
    });

    // Listen for messages from parent window
    window.addEventListener('message', (event) => {
      if (event.data.action === 'closeOverlay') {
        this.closeOverlay();
      }
    });

    // Handle clicks outside modal content
    document.addEventListener('click', (e) => {
      const target = e.target as HTMLElement;
      if (target.classList.contains('step-header')) {
        const stepElement = target.closest('.trace-step') as HTMLElement;
        if (stepElement) {
          this.toggleStepExpansion(stepElement);
        }
      }
    });
  }

  private connectToBackground(): void {
    try {
      // Connect to background for streaming updates
      const port = chrome.runtime.connect({ name: 'carbonlens-trace' });
      
      port.onMessage.addListener((message) => {
        if (message.type === 'task_started') {
          this.handleTaskStarted(message.taskId);
        } else if (message.type === 'delta') {
          this.handleStreamDelta(message.delta);
        } else if (message.type === 'task_completed') {
          this.handleTaskCompleted();
        }
      });

      port.onDisconnect.addListener(() => {
        console.log('Trace port disconnected');
      });

    } catch (error) {
      console.error('Failed to connect to background:', error);
    }
  }

  private handleTaskStarted(taskId: string): void {
    this.currentTaskId = taskId;
    this.clearTrace();
    this.updateStatus('Running');
    this.showTraceSteps();
  }

  private handleStreamDelta(delta: StreamDelta): void {
    const step: TraceStep = {
      id: `step_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      type: delta.type,
      title: this.getDeltaTitle(delta),
      content: delta,
      timestamp: Date.now(),
      expanded: false,
    };

    this.addStep(step);
  }

  private handleTaskCompleted(): void {
    this.updateStatus('Completed');
  }

  private getDeltaTitle(delta: StreamDelta): string {
    switch (delta.type) {
      case 'plan':
        return `🧠 Planning: ${delta.content.substring(0, 50)}...`;
      case 'tool_call':
        return `🔧 Tool Call: ${delta.content}`;
      case 'tool_result':
        return `📊 Tool Result: ${delta.content}`;
      case 'final':
        return `✅ Final Answer: ${delta.content.substring(0, 50)}...`;
      case 'error':
        return `❌ Error: ${delta.content}`;
      default:
        return delta.content;
    }
  }

  private addStep(step: TraceStep): void {
    this.steps.push(step);
    this.renderStep(step);
    
    if (this.autoScroll) {
      this.scrollToBottom();
    }
  }

  private renderStep(step: TraceStep): void {
    const stepElement = document.createElement('div');
    stepElement.className = `trace-step ${step.type}`;
    stepElement.setAttribute('data-step-id', step.id);

    const timestamp = new Date(step.timestamp).toLocaleTimeString();
    
    stepElement.innerHTML = `
      <div class="step-header">
        <div class="step-icon ${step.type}"></div>
        <div class="step-title">${step.title}</div>
        <div class="step-timestamp">${timestamp}</div>
        <button class="step-expand">▼</button>
      </div>
      <div class="step-content">
        ${this.renderStepContent(step)}
      </div>
    `;

    this.elements.traceSteps.appendChild(stepElement);
  }

  private renderStepContent(step: TraceStep): string {
    const delta = step.content as StreamDelta;
    let content = '';

    switch (delta.type) {
      case 'plan':
        content = `
          <h5>Planning Phase</h5>
          <div class="reasoning">${delta.content}</div>
          ${delta.data ? `<pre>${JSON.stringify(delta.data, null, 2)}</pre>` : ''}
        `;
        break;

      case 'tool_call':
        content = `
          <h5>Tool Execution</h5>
          <div class="tool-args">
            <strong>Tool:</strong> ${delta.content}<br>
            ${delta.data ? `<strong>Arguments:</strong><pre>${JSON.stringify(delta.data, null, 2)}</pre>` : ''}
          </div>
        `;
        break;

      case 'tool_result':
        content = `
          <h5>Tool Result</h5>
          <div class="tool-result">
            ${delta.content}
            ${delta.data ? `<pre>${JSON.stringify(delta.data, null, 2)}</pre>` : ''}
          </div>
        `;
        break;

      case 'final':
        content = `
          <h5>Final Answer</h5>
          <div class="reasoning">${delta.content}</div>
          ${delta.data ? `<pre>${JSON.stringify(delta.data, null, 2)}</pre>` : ''}
        `;
        break;

      case 'error':
        content = `
          <h5>Error</h5>
          <div class="error">
            ${delta.content}
            ${delta.data ? `<pre>${JSON.stringify(delta.data, null, 2)}</pre>` : ''}
          </div>
        `;
        break;

      default:
        content = `<pre>${JSON.stringify(delta, null, 2)}</pre>`;
    }

    return content;
  }

  private toggleStepExpansion(stepElement: HTMLElement): void {
    const stepId = stepElement.getAttribute('data-step-id');
    const step = this.steps.find(s => s.id === stepId);
    
    if (!step) return;

    const content = stepElement.querySelector('.step-content') as HTMLElement;
    const expandBtn = stepElement.querySelector('.step-expand') as HTMLElement;

    step.expanded = !step.expanded;
    
    if (step.expanded) {
      content.classList.add('expanded');
      expandBtn.classList.add('expanded');
    } else {
      content.classList.remove('expanded');
      expandBtn.classList.remove('expanded');
    }
  }

  private showTraceSteps(): void {
    this.elements.welcomeState.style.display = 'none';
    this.elements.traceSteps.classList.add('active');
  }

  private hideTraceSteps(): void {
    this.elements.welcomeState.style.display = 'flex';
    this.elements.traceSteps.classList.remove('active');
  }

  private clearTrace(): void {
    this.steps = [];
    this.elements.traceSteps.innerHTML = '';
    this.hideTraceSteps();
    this.updateStatus('Ready');
  }

  private exportTrace(): void {
    if (this.steps.length === 0) {
      alert('No trace data to export');
      return;
    }

    const traceData = {
      taskId: this.currentTaskId,
      timestamp: new Date().toISOString(),
      steps: this.steps.map(step => ({
        type: step.type,
        title: step.title,
        content: step.content,
        timestamp: step.timestamp,
      })),
    };

    const blob = new Blob([JSON.stringify(traceData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `carbonlens-trace-${this.currentTaskId || Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
  }

  private toggleAutoScroll(): void {
    this.autoScroll = !this.autoScroll;
    this.elements.toggleAutoScrollBtn.setAttribute('data-enabled', this.autoScroll.toString());
    
    if (this.autoScroll) {
      this.scrollToBottom();
    }
  }

  private scrollToBottom(): void {
    this.elements.traceContainer.scrollTop = this.elements.traceContainer.scrollHeight;
  }

  private updateStatus(status: string): void {
    this.elements.traceStatus.textContent = status;
    this.elements.traceStatus.className = `status ${status.toLowerCase()}`;
  }

  private closeOverlay(): void {
    // Send message to parent window to remove overlay
    if (window.parent !== window) {
      window.parent.postMessage({ action: 'closeOverlay' }, '*');
    } else {
      // Direct removal if not in iframe
      const overlay = document.getElementById('carbonlens-overlay');
      if (overlay) {
        overlay.remove();
      }
    }
  }

  // Public method to simulate trace steps (for testing)
  public simulateTrace(): void {
    const mockSteps: StreamDelta[] = [
      {
        type: 'plan',
        content: 'Analyzing request to compare carbon emissions between regions',
        data: { reasoning: 'Need to gather carbon factors for both regions' },
      },
      {
        type: 'tool_call',
        content: 'CarbonApiTool',
        data: { region: 'us-east-1', service: 'compute', instanceType: '8-vCPU' },
      },
      {
        type: 'tool_result',
        content: 'Retrieved carbon factor for us-east-1',
        data: { factor: 0.45, unit: 'kg CO2e/kWh' },
      },
      {
        type: 'tool_call',
        content: 'CarbonApiTool',
        data: { region: 'eu-west-1', service: 'compute', instanceType: '8-vCPU' },
      },
      {
        type: 'tool_result',
        content: 'Retrieved carbon factor for eu-west-1',
        data: { factor: 0.35, unit: 'kg CO2e/kWh' },
      },
      {
        type: 'tool_call',
        content: 'EmissionEstimatorTool',
        data: { scenarios: [{ region: 'us-east-1', instances: 200 }, { region: 'eu-west-1', instances: 200 }] },
      },
      {
        type: 'tool_result',
        content: 'Monte Carlo analysis completed',
        data: { results: { 'us-east-1': 180, 'eu-west-1': 140 } },
      },
      {
        type: 'final',
        content: 'Analysis complete: eu-west-1 has 22% lower emissions than us-east-1',
        data: { recommendation: 'Choose eu-west-1 for lower carbon footprint' },
      },
    ];

    this.handleTaskStarted('demo-task');
    
    mockSteps.forEach((delta, index) => {
      setTimeout(() => {
        this.handleStreamDelta(delta);
        if (index === mockSteps.length - 1) {
          setTimeout(() => this.handleTaskCompleted(), 500);
        }
      }, index * 1000);
    });
  }
}

// Initialize overlay when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
  const overlay = new CarbonLensOverlay();
  
  // Expose for testing
  (window as any).carbonLensOverlay = overlay;
});
