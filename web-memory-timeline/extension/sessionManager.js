// Pure utilities for session grouping and IDs

export function cryptoRandomId() {
  return Math.random().toString(36).slice(2, 10);
}

export function normalizeUrl(url) {
  try {
    const u = new URL(url);
    u.hash = "";
    return u.toString();
  } catch (e) {
    return url;
  }
}

export function findOrCreateSession(sessions, visit, thresholdMs = 15 * 60 * 1000) {
  if (!Array.isArray(sessions)) sessions = [];
  if (!sessions.length) {
    const newSession = {
      id: cryptoRandomId(),
      start: visit.ts,
      end: visit.ts,
      sessionTitle: visit.title || visit.url,
      pages: [
        {
          url: normalizeUrl(visit.url),
          title: visit.title || visit.url,
          snippet: visit.snippet || "",
          ts: visit.ts
        }
      ]
    };
    return { sessions: [newSession], session: newSession };
  }

  const last = sessions[sessions.length - 1];
  if (visit.ts - last.end <= thresholdMs) {
    // Same session; dedupe by URL within this session
    const normUrl = normalizeUrl(visit.url);
    const exists = last.pages.some((p) => normalizeUrl(p.url) === normUrl);
    if (!exists) {
      last.pages.push({
        url: normUrl,
        title: visit.title || visit.url,
        snippet: visit.snippet || "",
        ts: visit.ts
      });
      // Update end and sessionTitle heuristically
      last.end = visit.ts;
      if (visit.title) last.sessionTitle = last.sessionTitle || visit.title;
    } else {
      // Update timestamp if newer
      last.end = Math.max(last.end, visit.ts);
    }
    return { sessions, session: last };
  }

  // New session
  const newSession = {
    id: cryptoRandomId(),
    start: visit.ts,
    end: visit.ts,
    sessionTitle: visit.title || visit.url,
    pages: [
      {
        url: normalizeUrl(visit.url),
        title: visit.title || visit.url,
        snippet: visit.snippet || "",
        ts: visit.ts
      }
    ]
  };
  sessions.push(newSession);
  return { sessions, session: newSession };
}
