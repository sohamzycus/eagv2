# Web Memory Timeline — Chrome Extension (MV3)

Captures visited pages locally, groups into sessions with 15-minute idle gap, and exports `visits.json` for indexing (Colab or Supabase).

## Load Unpacked
1. Go to `chrome://extensions`
2. Enable Developer Mode
3. Click "Load unpacked" and select the `extension/` folder

## Permissions
- storage, tabs, scripting, activeTab
- host_permissions: <all_urls>

## Blacklist
Default blacklist includes common private domains (Gmail, WhatsApp, etc). You can edit the list in the popup (one rule per line). Rules support wildcard suffix like `*.bank.com`.

## Export
Click "Export JSON" in the popup to download `visits.json`. This will contain an array of sessions: `{ id, start, end, sessionTitle, pages: [{ url, title, snippet, ts }] }`.

## Privacy
- Nothing is uploaded automatically; data is kept in `chrome.storage.local`.
- Export is user-initiated.
