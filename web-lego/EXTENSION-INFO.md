# 🔍 Web Lego Extension - Access Information

## 🆔 How to Find Your Extension ID

### Method 1: From Chrome Extensions Page
1. Go to `chrome://extensions/`
2. Find "Web Lego - Modular Page Composer"
3. Click "Details"
4. The **Extension ID** is shown in the URL: `chrome://extensions/?id=YOUR_EXTENSION_ID_HERE`

### Method 2: From Developer Mode
1. Go to `chrome://extensions/`
2. Enable "Developer mode" (top-right toggle)
3. The **Extension ID** is displayed under the extension name

## 📺 How to Access Demo Page

### Easy Way (Recommended)
1. **Click the Web Lego extension icon** in your toolbar
2. **Click "📺 Open Demo Page"** button in the popup
3. Demo page opens automatically in a new tab!

### Manual Way (If needed)
1. **Find your Extension ID** using methods above
2. **Navigate to**: `chrome-extension://YOUR_EXTENSION_ID_HERE/demo-page.html`
3. Replace `YOUR_EXTENSION_ID_HERE` with your actual extension ID

### Example URLs
If your extension ID is `abcdefghijklmnopqrstuvwxyz123456`, then:
- **Canvas**: `chrome-extension://abcdefghijklmnopqrstuvwxyz123456/canvas.html`
- **Demo Page**: `chrome-extension://abcdefghijklmnopqrstuvwxyz123456/demo-page.html`

## 🛠️ Troubleshooting Extension Context Issues

### If you get "Extension context invalidated" errors:

#### Quick Fix
1. **Reload the extension**:
   - Go to `chrome://extensions/`
   - Find Web Lego extension
   - Click the **reload button** (🔄)

2. **Refresh the webpage** you're working on

3. **Try again** - the extension should work normally

#### Why This Happens
- Extension gets reloaded while you're using it
- Chrome invalidates the extension context
- Content scripts lose connection to extension APIs

#### Prevention
- Avoid reloading the extension while actively using it
- Close canvas tabs before reloading extension
- Keep extension stable during demo recordings

## 🎬 Demo Recording Setup

### Before Recording
1. **Install extension** in Developer Mode
2. **Test the demo button** - click Web Lego icon → "📺 Open Demo Page"
3. **Verify canvas opens** from demo page
4. **Practice the flow** once before recording

### Quick Demo Flow
1. **Open demo page** via popup button
2. **Activate Web Lego** on demo page
3. **Select elements** (hover + click)
4. **Add to canvas** (individual or "Add All")
5. **Show canvas features** (drag, edit, resize)
6. **Export options** (HTML, code, share)

### URLs for Reference
- **Extensions page**: `chrome://extensions/`
- **Demo page**: Click "📺 Open Demo Page" in popup
- **Canvas**: Opens automatically when you add elements

## 🔧 Common Issues & Solutions

### Issue: "Cannot access demo page"
**Solution**: Make sure extension is loaded and try the popup button

### Issue: "Canvas won't open"
**Solution**: 
1. Check if extension context is valid
2. Try reloading extension
3. Use the fallback modal if new tab fails

### Issue: "Extension ID not found"
**Solution**: 
1. Ensure extension is installed
2. Check Developer Mode is enabled
3. Look for the extension in chrome://extensions/

### Issue: "Demo page is blank"
**Solution**:
1. Reload the extension
2. Try opening via popup button
3. Check browser console for errors

---

**💡 Pro Tip**: Always use the "📺 Open Demo Page" button in the popup - it's the most reliable way to access the demo page and handles all URL generation automatically!
