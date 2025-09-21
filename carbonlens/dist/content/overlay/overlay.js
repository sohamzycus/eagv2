class CarbonLensOverlay {
  constructor() {
    this.steps = [];
    this.autoScroll = true;
    this.elements = {
      traceStatus: document.getElementById("traceStatus"),
      welcomeState: document.getElementById("welcomeState"),
      traceSteps: document.getElementById("traceSteps"),
      traceContainer: document.getElementById("traceContainer"),
      closeOverlay: document.getElementById("closeOverlay"),
      clearTraceBtn: document.getElementById("clearTraceBtn"),
      exportTraceBtn: document.getElementById("exportTraceBtn"),
      toggleAutoScrollBtn: document.getElementById("toggleAutoScrollBtn")
    };
    this.init();
  }
  init() {
    this.setupEventListeners();
    this.connectToBackground();
    this.updateStatus("Ready");
  }
  setupEventListeners() {
    this.elements.closeOverlay.addEventListener("click", () => {
      this.closeOverlay();
    });
    this.elements.clearTraceBtn.addEventListener("click", () => {
      this.clearTrace();
    });
    this.elements.exportTraceBtn.addEventListener("click", () => {
      this.exportTrace();
    });
    this.elements.toggleAutoScrollBtn.addEventListener("click", () => {
      this.toggleAutoScroll();
    });
    window.addEventListener("message", (event) => {
      if (event.data.action === "closeOverlay") {
        this.closeOverlay();
      }
    });
    document.addEventListener("click", (e) => {
      const target = e.target;
      if (target.classList.contains("step-header")) {
        const stepElement = target.closest(".trace-step");
        if (stepElement) {
          this.toggleStepExpansion(stepElement);
        }
      }
    });
  }
  connectToBackground() {
    try {
      const port = chrome.runtime.connect({ name: "carbonlens-trace" });
      port.onMessage.addListener((message) => {
        if (message.type === "task_started") {
          this.handleTaskStarted(message.taskId);
        } else if (message.type === "delta") {
          this.handleStreamDelta(message.delta);
        } else if (message.type === "task_completed") {
          this.handleTaskCompleted();
        }
      });
      port.onDisconnect.addListener(() => {
        console.log("Trace port disconnected");
      });
    } catch (error) {
      console.error("Failed to connect to background:", error);
    }
  }
  handleTaskStarted(taskId) {
    this.currentTaskId = taskId;
    this.clearTrace();
    this.updateStatus("Running");
    this.showTraceSteps();
  }
  handleStreamDelta(delta) {
    const step = {
      id: `step_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      type: delta.type,
      title: this.getDeltaTitle(delta),
      content: delta,
      timestamp: Date.now(),
      expanded: false
    };
    this.addStep(step);
  }
  handleTaskCompleted() {
    this.updateStatus("Completed");
  }
  getDeltaTitle(delta) {
    switch (delta.type) {
      case "plan":
        return `🧠 Planning: ${delta.content.substring(0, 50)}...`;
      case "tool_call":
        return `🔧 Tool Call: ${delta.content}`;
      case "tool_result":
        return `📊 Tool Result: ${delta.content}`;
      case "final":
        return `✅ Final Answer: ${delta.content.substring(0, 50)}...`;
      case "error":
        return `❌ Error: ${delta.content}`;
      default:
        return delta.content;
    }
  }
  addStep(step) {
    this.steps.push(step);
    this.renderStep(step);
    if (this.autoScroll) {
      this.scrollToBottom();
    }
  }
  renderStep(step) {
    const stepElement = document.createElement("div");
    stepElement.className = `trace-step ${step.type}`;
    stepElement.setAttribute("data-step-id", step.id);
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
  renderStepContent(step) {
    const delta = step.content;
    let content = "";
    switch (delta.type) {
      case "plan":
        content = `
          <h5>Planning Phase</h5>
          <div class="reasoning">${delta.content}</div>
          ${delta.data ? `<pre>${JSON.stringify(delta.data, null, 2)}</pre>` : ""}
        `;
        break;
      case "tool_call":
        content = `
          <h5>Tool Execution</h5>
          <div class="tool-args">
            <strong>Tool:</strong> ${delta.content}<br>
            ${delta.data ? `<strong>Arguments:</strong><pre>${JSON.stringify(delta.data, null, 2)}</pre>` : ""}
          </div>
        `;
        break;
      case "tool_result":
        content = `
          <h5>Tool Result</h5>
          <div class="tool-result">
            ${delta.content}
            ${delta.data ? `<pre>${JSON.stringify(delta.data, null, 2)}</pre>` : ""}
          </div>
        `;
        break;
      case "final":
        content = `
          <h5>Final Answer</h5>
          <div class="reasoning">${delta.content}</div>
          ${delta.data ? `<pre>${JSON.stringify(delta.data, null, 2)}</pre>` : ""}
        `;
        break;
      case "error":
        content = `
          <h5>Error</h5>
          <div class="error">
            ${delta.content}
            ${delta.data ? `<pre>${JSON.stringify(delta.data, null, 2)}</pre>` : ""}
          </div>
        `;
        break;
      default:
        content = `<pre>${JSON.stringify(delta, null, 2)}</pre>`;
    }
    return content;
  }
  toggleStepExpansion(stepElement) {
    const stepId = stepElement.getAttribute("data-step-id");
    const step = this.steps.find((s) => s.id === stepId);
    if (!step) return;
    const content = stepElement.querySelector(".step-content");
    const expandBtn = stepElement.querySelector(".step-expand");
    step.expanded = !step.expanded;
    if (step.expanded) {
      content.classList.add("expanded");
      expandBtn.classList.add("expanded");
    } else {
      content.classList.remove("expanded");
      expandBtn.classList.remove("expanded");
    }
  }
  showTraceSteps() {
    this.elements.welcomeState.style.display = "none";
    this.elements.traceSteps.classList.add("active");
  }
  hideTraceSteps() {
    this.elements.welcomeState.style.display = "flex";
    this.elements.traceSteps.classList.remove("active");
  }
  clearTrace() {
    this.steps = [];
    this.elements.traceSteps.innerHTML = "";
    this.hideTraceSteps();
    this.updateStatus("Ready");
  }
  exportTrace() {
    if (this.steps.length === 0) {
      alert("No trace data to export");
      return;
    }
    const traceData = {
      taskId: this.currentTaskId,
      timestamp: (/* @__PURE__ */ new Date()).toISOString(),
      steps: this.steps.map((step) => ({
        type: step.type,
        title: step.title,
        content: step.content,
        timestamp: step.timestamp
      }))
    };
    const blob = new Blob([JSON.stringify(traceData, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `carbonlens-trace-${this.currentTaskId || Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
  }
  toggleAutoScroll() {
    this.autoScroll = !this.autoScroll;
    this.elements.toggleAutoScrollBtn.setAttribute("data-enabled", this.autoScroll.toString());
    if (this.autoScroll) {
      this.scrollToBottom();
    }
  }
  scrollToBottom() {
    this.elements.traceContainer.scrollTop = this.elements.traceContainer.scrollHeight;
  }
  updateStatus(status) {
    this.elements.traceStatus.textContent = status;
    this.elements.traceStatus.className = `status ${status.toLowerCase()}`;
  }
  closeOverlay() {
    if (window.parent !== window) {
      window.parent.postMessage({ action: "closeOverlay" }, "*");
    } else {
      const overlay = document.getElementById("carbonlens-overlay");
      if (overlay) {
        overlay.remove();
      }
    }
  }
  // Public method to simulate trace steps (for testing)
  simulateTrace() {
    const mockSteps = [
      {
        type: "plan",
        content: "Analyzing request to compare carbon emissions between regions",
        data: { reasoning: "Need to gather carbon factors for both regions" }
      },
      {
        type: "tool_call",
        content: "CarbonApiTool",
        data: { region: "us-east-1", service: "compute", instanceType: "8-vCPU" }
      },
      {
        type: "tool_result",
        content: "Retrieved carbon factor for us-east-1",
        data: { factor: 0.45, unit: "kg CO2e/kWh" }
      },
      {
        type: "tool_call",
        content: "CarbonApiTool",
        data: { region: "eu-west-1", service: "compute", instanceType: "8-vCPU" }
      },
      {
        type: "tool_result",
        content: "Retrieved carbon factor for eu-west-1",
        data: { factor: 0.35, unit: "kg CO2e/kWh" }
      },
      {
        type: "tool_call",
        content: "EmissionEstimatorTool",
        data: { scenarios: [{ region: "us-east-1", instances: 200 }, { region: "eu-west-1", instances: 200 }] }
      },
      {
        type: "tool_result",
        content: "Monte Carlo analysis completed",
        data: { results: { "us-east-1": 180, "eu-west-1": 140 } }
      },
      {
        type: "final",
        content: "Analysis complete: eu-west-1 has 22% lower emissions than us-east-1",
        data: { recommendation: "Choose eu-west-1 for lower carbon footprint" }
      }
    ];
    this.handleTaskStarted("demo-task");
    mockSteps.forEach((delta, index) => {
      setTimeout(() => {
        this.handleStreamDelta(delta);
        if (index === mockSteps.length - 1) {
          setTimeout(() => this.handleTaskCompleted(), 500);
        }
      }, index * 1e3);
    });
  }
}
document.addEventListener("DOMContentLoaded", () => {
  const overlay = new CarbonLensOverlay();
  window.carbonLensOverlay = overlay;
});
