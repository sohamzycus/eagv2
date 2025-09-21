class CarbonLensPopup {
  constructor() {
    this.state = {
      isRunning: false,
      config: {
        useBackend: false,
        samples: 1e3
      }
    };
    this.elements = {
      taskInput: document.getElementById("taskInput"),
      runTaskBtn: document.getElementById("runTaskBtn"),
      cancelTaskBtn: document.getElementById("cancelTaskBtn"),
      statusIndicator: document.getElementById("statusIndicator"),
      statusText: document.getElementById("statusText"),
      taskStatus: document.getElementById("taskStatus"),
      progressFill: document.getElementById("progressFill"),
      progressText: document.getElementById("progressText"),
      resultsContainer: document.getElementById("resultsContainer"),
      resultsContent: document.getElementById("resultsContent"),
      settingsBtn: document.getElementById("settingsBtn"),
      exportBtn: document.getElementById("exportBtn"),
      closeResultsBtn: document.getElementById("closeResultsBtn"),
      openOverlayBtn: document.getElementById("openOverlayBtn"),
      viewHistoryBtn: document.getElementById("viewHistoryBtn"),
      useMonteCarlo: document.getElementById("useMonteCarlo"),
      sampleSize: document.getElementById("sampleSize"),
      useBackend: document.getElementById("useBackend")
    };
    this.init();
  }
  async init() {
    this.setupEventListeners();
    this.setupSamplePrompts();
    await this.loadConfig();
    this.updateUI();
  }
  setupEventListeners() {
    this.elements.runTaskBtn.addEventListener("click", () => this.runTask());
    this.elements.cancelTaskBtn.addEventListener("click", () => this.cancelTask());
    this.elements.settingsBtn.addEventListener("click", () => this.openSettings());
    this.elements.exportBtn.addEventListener("click", () => this.exportLogs());
    this.elements.closeResultsBtn.addEventListener("click", () => this.closeResults());
    this.elements.openOverlayBtn.addEventListener("click", () => this.openOverlay());
    this.elements.viewHistoryBtn.addEventListener("click", () => this.viewHistory());
    this.elements.useBackend.addEventListener("change", () => this.updateConfig());
    this.elements.sampleSize.addEventListener("change", () => this.updateConfig());
    this.elements.taskInput.addEventListener("input", () => this.validateInput());
    this.elements.taskInput.addEventListener("keydown", (e) => {
      if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) {
        e.preventDefault();
        this.runTask();
      }
    });
  }
  setupSamplePrompts() {
    const promptButtons = document.querySelectorAll(".prompt-btn");
    promptButtons.forEach((btn) => {
      btn.addEventListener("click", () => {
        const prompt = btn.getAttribute("data-prompt");
        if (prompt) {
          this.elements.taskInput.value = prompt;
          this.validateInput();
        }
      });
    });
  }
  async loadConfig() {
    try {
      const response = await chrome.runtime.sendMessage({ action: "getConfig" });
      if (response.success) {
        this.state.config.useBackend = response.config.useRealMode && !!response.config.backendUrl;
        this.elements.useBackend.checked = this.state.config.useBackend;
      }
    } catch (error) {
      console.error("Failed to load config:", error);
    }
  }
  updateConfig() {
    this.state.config.useBackend = this.elements.useBackend.checked;
    this.state.config.samples = parseInt(this.elements.sampleSize.value) || 1e3;
  }
  validateInput() {
    const hasInput = this.elements.taskInput.value.trim().length > 0;
    this.elements.runTaskBtn.disabled = !hasInput || this.state.isRunning;
  }
  async runTask() {
    const prompt = this.elements.taskInput.value.trim();
    if (!prompt || this.state.isRunning) return;
    this.state.isRunning = true;
    this.updateUI();
    const taskRequest = {
      prompt,
      samples: this.elements.useMonteCarlo.checked ? this.state.config.samples : void 0,
      useBackend: this.state.config.useBackend
    };
    try {
      const port = chrome.runtime.connect({ name: "carbonlens-stream" });
      port.postMessage({
        action: "startStreamingTask",
        taskRequest
      });
      port.onMessage.addListener((message) => {
        if (message.type === "started") {
          this.state.currentTaskId = message.taskId;
        } else if (message.type === "delta") {
          this.handleStreamDelta(message.delta);
        } else if (message.type === "error") {
          this.handleError(message.error);
        }
      });
      port.onDisconnect.addListener(() => {
        if (this.state.isRunning) {
          this.handleError("Connection lost");
        }
      });
    } catch (error) {
      this.handleError(error.message);
    }
  }
  handleStreamDelta(delta) {
    switch (delta.type) {
      case "plan":
        this.updateProgress(delta.content, 25);
        break;
      case "tool_call":
        this.updateProgress(delta.content, 50);
        break;
      case "tool_result":
        this.updateProgress(delta.content, 75);
        break;
      case "final":
        this.handleTaskComplete(delta.data);
        break;
      case "error":
        this.handleError(delta.content);
        break;
    }
  }
  updateProgress(text, percentage) {
    this.elements.progressText.textContent = text;
    this.elements.progressFill.style.width = `${percentage}%`;
  }
  async handleTaskComplete(result) {
    this.state.isRunning = false;
    this.updateProgress("Task completed", 100);
    setTimeout(() => {
      this.showResults(result);
      this.updateUI();
    }, 500);
  }
  handleError(error) {
    this.state.isRunning = false;
    this.updateStatus("error", `Error: ${error}`);
    this.updateUI();
  }
  showResults(result) {
    this.elements.resultsContent.innerHTML = this.formatResult(result);
    this.elements.resultsContainer.style.display = "block";
    this.elements.taskStatus.style.display = "none";
  }
  formatResult(result) {
    if (!result.success) {
      return `<div class="error">Task failed: ${result.error}</div>`;
    }
    const response = result.result?.response || "No response available";
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
            <span class="value">${((result.metadata.endTime - result.metadata.startTime) / 1e3).toFixed(1)}s</span>
          </div>
        </div>
      </div>
    `;
  }
  formatMarkdown(text) {
    return text.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>").replace(/\*(.*?)\*/g, "<em>$1</em>").replace(/^# (.*$)/gm, "<h1>$1</h1>").replace(/^## (.*$)/gm, "<h2>$1</h2>").replace(/^### (.*$)/gm, "<h3>$1</h3>").replace(/^- (.*$)/gm, "<li>$1</li>").replace(/(<li>.*<\/li>)/gs, "<ul>$1</ul>").replace(/\n\n/g, "</p><p>").replace(/^(.+)$/gm, "<p>$1</p>").replace(/<p><\/p>/g, "");
  }
  async cancelTask() {
    if (this.state.currentTaskId) {
      try {
        await chrome.runtime.sendMessage({
          action: "cancelTask",
          taskId: this.state.currentTaskId
        });
      } catch (error) {
        console.error("Failed to cancel task:", error);
      }
    }
    this.state.isRunning = false;
    this.state.currentTaskId = void 0;
    this.updateUI();
  }
  closeResults() {
    this.elements.resultsContainer.style.display = "none";
  }
  async exportLogs() {
    if (!this.state.currentTaskId) return;
    try {
      const response = await chrome.runtime.sendMessage({
        action: "exportTaskLogs",
        taskId: this.state.currentTaskId
      });
      if (response.success) {
        const blob = new Blob([response.logs], { type: "text/plain" });
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `carbonlens-task-${this.state.currentTaskId}.txt`;
        a.click();
        URL.revokeObjectURL(url);
      }
    } catch (error) {
      console.error("Failed to export logs:", error);
    }
  }
  openSettings() {
    chrome.runtime.openOptionsPage();
  }
  async openOverlay() {
    try {
      const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
      if (tab && tab.id) {
        await chrome.scripting.executeScript({
          target: { tabId: tab.id },
          func: () => {
            if (document.getElementById("carbonlens-overlay")) return;
            const overlay = document.createElement("iframe");
            overlay.id = "carbonlens-overlay";
            overlay.src = chrome.runtime.getURL("content/overlay/overlay.html");
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
          }
        });
      }
    } catch (error) {
      console.error("Failed to open overlay:", error);
    }
  }
  viewHistory() {
    console.log("View history - to be implemented");
  }
  updateStatus(type, text) {
    this.elements.statusIndicator.className = `status-indicator ${type}`;
    this.elements.statusText.textContent = text;
  }
  updateUI() {
    if (this.state.isRunning) {
      this.updateStatus("running", "Running analysis...");
      this.elements.taskStatus.style.display = "block";
    } else {
      this.updateStatus("ready", "Ready");
      this.elements.taskStatus.style.display = "none";
    }
    this.validateInput();
    this.elements.cancelTaskBtn.disabled = !this.state.isRunning;
    this.elements.exportBtn.disabled = !this.state.currentTaskId;
  }
}
document.addEventListener("DOMContentLoaded", () => {
  new CarbonLensPopup();
});
