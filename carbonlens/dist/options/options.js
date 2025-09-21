class CarbonLensOptions {
  constructor() {
    this.state = {
      config: {
        useRealMode: false,
        notificationChannels: []
      },
      isDirty: false
    };
    this.elements = {
      mockMode: document.getElementById("mockMode"),
      realMode: document.getElementById("realMode"),
      backendUrl: document.getElementById("backendUrl"),
      geminiKey: document.getElementById("geminiKey"),
      carbonInterfaceKey: document.getElementById("carbonInterfaceKey"),
      climatiqKey: document.getElementById("climatiqKey"),
      electricityMapKey: document.getElementById("electricityMapKey"),
      newsApiKey: document.getElementById("newsApiKey"),
      testBackendBtn: document.getElementById("testBackendBtn"),
      backendTestResult: document.getElementById("backendTestResult"),
      saveBtn: document.getElementById("saveBtn"),
      resetBtn: document.getElementById("resetBtn"),
      exportConfigBtn: document.getElementById("exportConfigBtn"),
      statusMessage: document.getElementById("statusMessage"),
      backendSection: document.getElementById("backendSection"),
      apiKeysSection: document.getElementById("apiKeysSection"),
      notificationChannels: document.getElementById("notificationChannels"),
      addChannelBtn: document.getElementById("addChannelBtn"),
      addChannelModal: document.getElementById("addChannelModal"),
      closeModalBtn: document.getElementById("closeModalBtn"),
      cancelChannelBtn: document.getElementById("cancelChannelBtn"),
      confirmAddChannelBtn: document.getElementById("confirmAddChannelBtn"),
      channelType: document.getElementById("channelType"),
      channelName: document.getElementById("channelName"),
      channelEndpoint: document.getElementById("channelEndpoint")
    };
    this.init();
  }
  async init() {
    await this.loadConfig();
    this.setupEventListeners();
    this.updateUI();
  }
  async loadConfig() {
    try {
      const response = await chrome.runtime.sendMessage({ action: "getConfig" });
      if (response.success) {
        this.state.config = { ...this.state.config, ...response.config };
      }
    } catch (error) {
      console.error("Failed to load config:", error);
    }
  }
  setupEventListeners() {
    this.elements.mockMode.addEventListener("change", () => this.onModeChange());
    this.elements.realMode.addEventListener("change", () => this.onModeChange());
    const inputs = [
      this.elements.backendUrl,
      this.elements.geminiKey,
      this.elements.carbonInterfaceKey,
      this.elements.climatiqKey,
      this.elements.electricityMapKey,
      this.elements.newsApiKey
    ];
    inputs.forEach((input) => {
      input.addEventListener("input", () => this.markDirty());
    });
    document.querySelectorAll(".toggle-visibility").forEach((btn) => {
      btn.addEventListener("click", (e) => {
        const target = e.target.getAttribute("data-target");
        if (target) {
          const input = document.getElementById(target);
          if (input.type === "password") {
            input.type = "text";
            e.target.textContent = "🙈";
          } else {
            input.type = "password";
            e.target.textContent = "👁️";
          }
        }
      });
    });
    this.elements.testBackendBtn.addEventListener("click", () => this.testBackend());
    this.elements.saveBtn.addEventListener("click", () => this.saveConfig());
    this.elements.resetBtn.addEventListener("click", () => this.resetConfig());
    this.elements.exportConfigBtn.addEventListener("click", () => this.exportConfig());
    this.elements.addChannelBtn.addEventListener("click", () => this.openAddChannelModal());
    this.elements.closeModalBtn.addEventListener("click", () => this.closeAddChannelModal());
    this.elements.cancelChannelBtn.addEventListener("click", () => this.closeAddChannelModal());
    this.elements.confirmAddChannelBtn.addEventListener("click", () => this.addNotificationChannel());
    this.elements.addChannelModal.addEventListener("click", (e) => {
      if (e.target === this.elements.addChannelModal) {
        this.closeAddChannelModal();
      }
    });
  }
  onModeChange() {
    this.state.config.useRealMode = this.elements.realMode.checked;
    this.markDirty();
    this.updateUI();
  }
  markDirty() {
    this.state.isDirty = true;
    this.elements.saveBtn.textContent = "Save Settings *";
    this.elements.saveBtn.style.background = "linear-gradient(135deg, #ed8936 0%, #dd6b20 100%)";
  }
  updateUI() {
    this.elements.mockMode.checked = !this.state.config.useRealMode;
    this.elements.realMode.checked = this.state.config.useRealMode;
    if (this.state.config.useRealMode) {
      this.elements.backendSection.classList.remove("hidden");
      this.elements.apiKeysSection.classList.remove("hidden");
    } else {
      this.elements.backendSection.classList.add("hidden");
      this.elements.apiKeysSection.classList.add("hidden");
    }
    this.elements.backendUrl.value = this.state.config.backendUrl || "";
    this.elements.geminiKey.value = this.state.config.apiKeys?.gemini || "";
    this.elements.carbonInterfaceKey.value = this.state.config.apiKeys?.carbonInterface || "";
    this.elements.climatiqKey.value = this.state.config.apiKeys?.climatiq || "";
    this.elements.electricityMapKey.value = this.state.config.apiKeys?.electricityMap || "";
    this.elements.newsApiKey.value = this.state.config.apiKeys?.newsApi || "";
    this.renderNotificationChannels();
  }
  renderNotificationChannels() {
    const channels = this.state.config.notificationChannels || [];
    if (channels.length === 0) {
      this.elements.notificationChannels.innerHTML = `
        <div class="empty-state">
          <span class="icon">📢</span>
          <p>No notification channels configured</p>
          <button class="add-btn" id="addChannelBtn">Add Channel</button>
        </div>
      `;
      document.getElementById("addChannelBtn")?.addEventListener("click", () => this.openAddChannelModal());
    } else {
      this.elements.notificationChannels.innerHTML = channels.map((channel, index) => `
        <div class="channel-item">
          <div class="channel-info">
            <span class="channel-type">${channel.type}</span>
            <span class="channel-name">${channel.name || "Unnamed"}</span>
            <small>${channel.endpoint}</small>
          </div>
          <button class="remove-channel" data-index="${index}">Remove</button>
        </div>
      `).join("") + `
        <button class="add-btn" id="addChannelBtn">Add Another Channel</button>
      `;
      document.getElementById("addChannelBtn")?.addEventListener("click", () => this.openAddChannelModal());
      document.querySelectorAll(".remove-channel").forEach((btn) => {
        btn.addEventListener("click", (e) => {
          const index = parseInt(e.target.getAttribute("data-index") || "0");
          this.removeNotificationChannel(index);
        });
      });
    }
  }
  async testBackend() {
    const url = this.elements.backendUrl.value.trim();
    if (!url) {
      this.showTestResult("error", "Please enter a backend URL");
      return;
    }
    this.elements.testBackendBtn.disabled = true;
    this.elements.testBackendBtn.textContent = "Testing...";
    try {
      const response = await fetch(`${url}/health`, {
        method: "GET",
        headers: { "Content-Type": "application/json" }
      });
      if (response.ok) {
        const data = await response.json();
        this.showTestResult("success", `✅ Connected successfully! Version: ${data.version || "unknown"}`);
      } else {
        this.showTestResult("error", `❌ Connection failed: ${response.status} ${response.statusText}`);
      }
    } catch (error) {
      this.showTestResult("error", `❌ Connection failed: ${error.message}`);
    } finally {
      this.elements.testBackendBtn.disabled = false;
      this.elements.testBackendBtn.textContent = "Test Connection";
    }
  }
  showTestResult(type, message) {
    this.elements.backendTestResult.className = `test-result ${type}`;
    this.elements.backendTestResult.textContent = message;
    this.elements.backendTestResult.style.display = "block";
    setTimeout(() => {
      this.elements.backendTestResult.style.display = "none";
    }, 5e3);
  }
  async saveConfig() {
    const config = {
      useRealMode: this.elements.realMode.checked,
      backendUrl: this.elements.backendUrl.value.trim() || void 0,
      apiKeys: {
        gemini: this.elements.geminiKey.value.trim() || void 0,
        carbonInterface: this.elements.carbonInterfaceKey.value.trim() || void 0,
        climatiq: this.elements.climatiqKey.value.trim() || void 0,
        electricityMap: this.elements.electricityMapKey.value.trim() || void 0,
        newsApi: this.elements.newsApiKey.value.trim() || void 0
      },
      notificationChannels: this.state.config.notificationChannels
    };
    if (config.apiKeys) {
      Object.keys(config.apiKeys).forEach((key) => {
        if (!config.apiKeys[key]) {
          delete config.apiKeys[key];
        }
      });
    }
    try {
      const response = await chrome.runtime.sendMessage({
        action: "updateConfig",
        config
      });
      if (response.success) {
        this.state.config = config;
        this.state.isDirty = false;
        this.elements.saveBtn.textContent = "Save Settings";
        this.elements.saveBtn.style.background = "linear-gradient(135deg, #667eea 0%, #764ba2 100%)";
        this.showStatus("success", "✅ Settings saved successfully!");
      } else {
        this.showStatus("error", "❌ Failed to save settings");
      }
    } catch (error) {
      this.showStatus("error", `❌ Error: ${error.message}`);
    }
  }
  async resetConfig() {
    if (!confirm("Are you sure you want to reset all settings to defaults?")) {
      return;
    }
    const defaultConfig = {
      useRealMode: false,
      notificationChannels: []
    };
    try {
      const response = await chrome.runtime.sendMessage({
        action: "updateConfig",
        config: defaultConfig
      });
      if (response.success) {
        this.state.config = defaultConfig;
        this.state.isDirty = false;
        this.updateUI();
        this.showStatus("success", "✅ Settings reset to defaults");
      }
    } catch (error) {
      this.showStatus("error", `❌ Error: ${error.message}`);
    }
  }
  exportConfig() {
    const configToExport = {
      ...this.state.config,
      apiKeys: this.state.config.apiKeys ? Object.fromEntries(
        Object.entries(this.state.config.apiKeys).map(
          ([key, value]) => [key, value ? "[REDACTED]" : void 0]
        )
      ) : void 0
    };
    const blob = new Blob([JSON.stringify(configToExport, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "carbonlens-config.json";
    a.click();
    URL.revokeObjectURL(url);
    this.showStatus("success", "✅ Configuration exported (API keys redacted)");
  }
  openAddChannelModal() {
    this.elements.addChannelModal.style.display = "flex";
    this.elements.channelName.value = "";
    this.elements.channelEndpoint.value = "";
    this.elements.channelType.value = "slack";
  }
  closeAddChannelModal() {
    this.elements.addChannelModal.style.display = "none";
  }
  addNotificationChannel() {
    const type = this.elements.channelType.value;
    const name = this.elements.channelName.value.trim();
    const endpoint = this.elements.channelEndpoint.value.trim();
    if (!name || !endpoint) {
      alert("Please fill in all fields");
      return;
    }
    const channel = { type, name, endpoint };
    if (!this.state.config.notificationChannels) {
      this.state.config.notificationChannels = [];
    }
    this.state.config.notificationChannels.push(channel);
    this.markDirty();
    this.renderNotificationChannels();
    this.closeAddChannelModal();
  }
  removeNotificationChannel(index) {
    if (this.state.config.notificationChannels) {
      this.state.config.notificationChannels.splice(index, 1);
      this.markDirty();
      this.renderNotificationChannels();
    }
  }
  showStatus(type, message) {
    this.elements.statusMessage.className = `status-message ${type}`;
    this.elements.statusMessage.textContent = message;
    this.elements.statusMessage.style.display = "block";
    setTimeout(() => {
      this.elements.statusMessage.style.display = "none";
    }, 3e3);
  }
}
document.addEventListener("DOMContentLoaded", () => {
  new CarbonLensOptions();
});
