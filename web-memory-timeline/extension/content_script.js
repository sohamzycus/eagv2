// Extract visible text using TreeWalker and send minimal payload to background
(function () {
  function getVisibleText(maxChars = 20000) {
    try {
      const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT, {
        acceptNode: function (node) {
          if (!node || !node.parentElement) return NodeFilter.FILTER_REJECT;
          const style = window.getComputedStyle(node.parentElement);
          if (!style) return NodeFilter.FILTER_REJECT;
          const hidden = style.display === "none" || style.visibility === "hidden" || style.opacity === "0";
          if (hidden) return NodeFilter.FILTER_REJECT;
          const text = node.nodeValue ? node.nodeValue.trim() : "";
          if (!text) return NodeFilter.FILTER_REJECT;
          return NodeFilter.FILTER_ACCEPT;
        }
      });
      let text = "";
      let node;
      while ((node = walker.nextNode())) {
        text += node.nodeValue + " ";
        if (text.length > maxChars) break;
      }
      return text.slice(0, maxChars).trim();
    } catch (e) {
      return document.body ? (document.body.innerText || "") : "";
    }
  }

  function makeSnippet(text, maxLen = 300) {
    if (!text) return "";
    return text.slice(0, maxLen).replace(/\s+/g, " ").trim();
  }

  function isBlacklisted(url, blacklist) {
    try {
      const u = new URL(url);
      const host = u.hostname || "";
      return blacklist.some((rule) => {
        const r = rule.trim().toLowerCase();
        if (!r) return false;
        if (r.startsWith("*")) {
          // wildcard suffix
          return host.toLowerCase().endsWith(r.slice(1));
        }
        return host.toLowerCase() === r || host.toLowerCase().includes(r);
      });
    } catch (e) {
      return false;
    }
  }

  async function runCapture() {
    try {
      const text = getVisibleText();
      const snippet = makeSnippet(text);
      const payload = {
        type: "PAGE_CAPTURE",
        url: location.href,
        title: document.title,
        snippet,
        ts: Date.now()
      };
      chrome.runtime.sendMessage(payload);
    } catch (e) {
      // no-op
    }
  }

  // Trigger after load idle
  if (document.readyState === "complete" || document.readyState === "interactive") {
    setTimeout(runCapture, 800);
  } else {
    window.addEventListener("DOMContentLoaded", () => setTimeout(runCapture, 800));
  }
})();
