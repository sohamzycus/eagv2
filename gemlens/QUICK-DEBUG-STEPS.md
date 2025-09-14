# 🚨 GemLens Quick Debug Steps

## 🔄 **STEP 1: Force Reload Extension**

1. **Go to**: `chrome://extensions/`
2. **Find GemLens** in the list
3. **Click the reload button** (🔄 circular arrow)
4. **Wait 2-3 seconds** for reload to complete

## 🧪 **STEP 2: Test Content Extraction**

1. **Go to Netflix page**: `netflixtechblog.com/uda-unified-data-architecture-6a6aee261d8d`
2. **Open browser console**: Press `F12` → Console tab
3. **Copy and paste this code**:

```javascript
// Test content extraction
console.log('=== Testing GemLens Content Extraction ===');

const contentSelectors = ['article', 'main', '[role="main"]', '.content', '#content'];
let found = false;

contentSelectors.forEach(selector => {
    const element = document.querySelector(selector);
    if (element) {
        console.log(`✅ Found content with "${selector}":`, element.textContent.length, 'characters');
        console.log('Preview:', element.textContent.substring(0, 200) + '...');
        found = true;
    } else {
        console.log(`❌ No content found with "${selector}"`);
    }
});

if (!found) {
    console.log('🔄 Fallback to body content');
    console.log('Body content length:', document.body.textContent.length);
}
```

4. **Check the output** - you should see content found

## 🎯 **STEP 3: Test Extension**

1. **Click GemLens icon** in toolbar
2. **Click "Summarize Page"**
3. **Watch for**:
   - Loading message changes
   - Console logs (keep F12 open)
   - Badge notification (✓ appears on extension icon)

## 🔍 **STEP 4: Debug Console Logs**

**Open console and look for these logs**:
- `GemLens: Extracting page content...`
- `Extracted content length: XXXX`
- `Extracted content preview: ...`
- `GemLens: Generating summary... (XXXX chars extracted)`
- `Summary received: XXXX characters`

## 🚨 **Common Issues & Fixes**

### Issue: "Extracting page content..." hangs
**Fix**: 
- Check console for errors
- Try refreshing the page first
- Make sure you reloaded the extension

### Issue: Popup disappears when switching tabs
**Fix**: 
- This is normal Chrome behavior
- Watch for the ✓ badge on extension icon
- Click extension icon again to see results

### Issue: No new UI elements (history button, etc.)
**Fix**:
- Make sure you reloaded the extension
- Clear browser cache: `Ctrl+Shift+R`
- Check if `dist/popup/popup.html` contains "history-container"

## 🎯 **Expected Results**

After fixing:
- ✅ Content extraction completes in 2-3 seconds
- ✅ Summary appears in popup with 📚 history button
- ✅ Badge shows ✓ when complete
- ✅ Console shows extraction details
- ✅ History button works (shows past summaries)

## 🆘 **If Still Not Working**

1. **Check API key**: Go to Settings → Test Connection
2. **Try simple page**: Use the debug-test.html file first
3. **Check permissions**: Extension should have "activeTab" and "scripting"
4. **Console errors**: Look for red errors in F12 console

## 📞 **Debug Commands**

Run these in console to check extension state:

```javascript
// Check if extension is loaded
console.log('Extension ID:', chrome.runtime.id);

// Check stored data
chrome.storage.local.get(null, console.log);

// Test API key
chrome.runtime.sendMessage({action: 'checkApiKey'}, console.log);
```
