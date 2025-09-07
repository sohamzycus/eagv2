# 🧪 Quick Test - Verify Extension Works

## ✅ Step-by-Step Test

### 1. Load Extension
- Go to `chrome://extensions/`
- Enable Developer Mode
- Click "Load unpacked" 
- Select the `web-lego/` folder
- ✅ Extension should load without errors

### 2. Test Demo Page Access
- Click Web Lego extension icon
- Click "📺 Open Demo Page" button
- ✅ Demo page should open in new tab

### 3. Test Basic Functionality
- On demo page, click Web Lego icon
- Click "Activate Web Lego"
- ✅ Floating toolbar should appear

### 4. Test Element Selection
- Click "Select" in toolbar
- Hover over elements
- ✅ Elements should highlight in blue
- Click elements
- ✅ Elements should turn green with checkmarks

### 5. Test Add Selected
- Select 2-3 elements
- Click "Add Selected"
- ✅ Should show "Added X blocks to canvas!"
- ✅ Canvas should open in new tab

### 6. Test Add All
- Go back to demo page
- Click "Add All" in toolbar
- ✅ Should show "Added X elements from this page!"
- ✅ Canvas should open with many blocks

### 7. Test Canvas Features
- In canvas, try:
  - Dragging blocks ✅
  - Resizing blocks ✅ 
  - Double-clicking to edit ✅
  - Deleting blocks ✅

### 8. Test Export
- Click "Export Layout"
- Try each export option:
  - HTML File ✅ (should download)
  - Code Export ✅ (should show modal with code)
  - Share Link ✅ (should copy to clipboard)
- ✅ Modal should close properly

## 🚨 If Any Test Fails

1. **Check browser console** for error messages
2. **Reload the extension** (chrome://extensions/)
3. **Refresh the webpage** you're testing on
4. **Try again**

## 🎯 Expected Results

If all tests pass:
- ✅ Extension loads without errors
- ✅ Demo page opens easily
- ✅ All toolbar buttons work
- ✅ Selection system works smoothly
- ✅ Canvas opens and functions properly
- ✅ All export options work
- ✅ No console errors

**If all tests pass, the extension is ready for demo recording!** 🎬

---

## 📞 Quick Debug Commands

Open browser console (F12) and run these to check status:

```javascript
// Check if Web Lego is loaded
console.log('Web Lego initialized:', window.webLegoInitialized);

// Check if Web Lego is active
console.log('Web Lego active:', window.webLegoActive);

// Check extension context
console.log('Chrome runtime:', !!chrome?.runtime?.id);

// Check storage
chrome.storage.local.get('webLegoBlocks').then(console.log);
```

These commands will help identify any remaining issues quickly.
