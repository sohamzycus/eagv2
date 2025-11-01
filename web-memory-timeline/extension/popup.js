function $(id) { return document.getElementById(id); }

function refreshStats() {
  chrome.runtime.sendMessage({ type: 'GET_STATS' }, (res) => {
    if (!res) return;
    $('sessionsCount').textContent = String(res.sessionsCount || 0);
    $('pagesCount').textContent = String(res.pagesCount || 0);
  });
}

function loadBlacklist() {
  chrome.runtime.sendMessage({ type: 'GET_BLACKLIST' }, (res) => {
    if (!res) return;
    const list = Array.isArray(res.blacklist) ? res.blacklist : [];
    $('blacklist').value = list.join('\n');
  });
}

function saveBlacklist() {
  const raw = $('blacklist').value || '';
  const list = raw.split(/\n|,/).map((s) => s.trim()).filter(Boolean);
  chrome.runtime.sendMessage({ type: 'SET_BLACKLIST', blacklist: list }, () => {
    // saved
  });
}

function exportVisits() {
  chrome.runtime.sendMessage({ type: 'EXPORT_VISITS' }, () => {});
}

function clearVisits() {
  chrome.runtime.sendMessage({ type: 'CLEAR_VISITS' }, () => {
    refreshStats();
  });
}

document.addEventListener('DOMContentLoaded', () => {
  refreshStats();
  loadBlacklist();
  $('saveBlacklist').addEventListener('click', saveBlacklist);
  $('exportBtn').addEventListener('click', exportVisits);
  $('clearBtn').addEventListener('click', clearVisits);
});
