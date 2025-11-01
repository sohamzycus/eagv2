importScripts('sessionManager.js');

const DEFAULT_BLACKLIST = [
  'mail.google.com',
  'accounts.google.com',
  'gmail.com',
  'web.whatsapp.com',
  'whatsapp.com',
  'teams.microsoft.com',
  'slack.com',
  'drive.google.com',
  'docs.google.com',
  'notion.so',
  'bank',
  'pay',
  'localhost'
];

async function getState() {
  const { sessions = [], blacklist = DEFAULT_BLACKLIST } = await chrome.storage.local.get(['sessions', 'blacklist']);
  return { sessions, blacklist };
}

async function setState(state) {
  await chrome.storage.local.set(state);
}

chrome.runtime.onInstalled.addListener(async () => {
  const { blacklist } = await chrome.storage.local.get(['blacklist']);
  if (!Array.isArray(blacklist)) {
    await chrome.storage.local.set({ blacklist: DEFAULT_BLACKLIST });
  }
});

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  (async () => {
    try {
      if (message && message.type === 'PAGE_CAPTURE') {
        const { sessions, blacklist } = await getState();
        // Basic blacklist check by hostname substring/wildcard
        try {
          const u = new URL(message.url);
          const host = u.hostname.toLowerCase();
          const blocked = blacklist.some((rule) => {
            const r = String(rule || '').trim().toLowerCase();
            if (!r) return false;
            if (r.startsWith('*')) return host.endsWith(r.slice(1));
            return host === r || host.includes(r);
          });
          if (blocked) return;
        } catch (e) {}

        const visit = {
          url: message.url,
          title: message.title,
          snippet: message.snippet,
          ts: message.ts || Date.now()
        };
        const result = findOrCreateSession(sessions, visit, 15 * 60 * 1000);
        await setState({ sessions: result.sessions });
        return;
      }

      if (message && message.type === 'GET_STATS') {
        const { sessions } = await getState();
        const totalPages = sessions.reduce((acc, s) => acc + (s.pages?.length || 0), 0);
        sendResponse({ sessionsCount: sessions.length, pagesCount: totalPages });
        return;
      }

      if (message && message.type === 'GET_BLACKLIST') {
        const { blacklist } = await getState();
        sendResponse({ blacklist });
        return;
      }

      if (message && message.type === 'SET_BLACKLIST') {
        const list = Array.isArray(message.blacklist)
          ? message.blacklist
          : String(message.blacklist || '')
              .split(/\n|,/) // allow newline or comma separated
              .map((s) => s.trim())
              .filter(Boolean);
        await setState({ blacklist: list });
        sendResponse({ ok: true });
        return;
      }

      if (message && message.type === 'EXPORT_VISITS') {
        const { sessions } = await getState();
        const blob = new Blob([JSON.stringify(sessions, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        chrome.downloads.download({ url, filename: 'visits.json', saveAs: true });
        sendResponse({ ok: true });
        return;
      }

      if (message && message.type === 'CLEAR_VISITS') {
        await setState({ sessions: [] });
        sendResponse({ ok: true });
        return;
      }
    } catch (e) {
      sendResponse({ ok: false, error: String(e) });
    }
  })();
  // keep channel open for async
  return true;
});
