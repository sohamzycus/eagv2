# 🔧 Web Lego Extension - Troubleshooting

## ✅ Quick Fix for Common Errors

### Error: "Service worker registration failed. Status code: 15"
**Solution**: This has been fixed! The issue was in background.js with conflicting event listeners.

### Error: "Cannot read properties of undefined (reading 'onClicked')"
**Solution**: This has been fixed! Removed problematic context menu and action listeners.

## 🚀 Steps to Fix Installation Issues

### Step 1: Clear Previous Installation
1. Go to `chrome://extensions/`
2. Remove any existing "Web Lego" extension
3. Click "Clear all" in the Errors section

### Step 2: Reload Extension
1. Click "Load unpacked" again
2. Select the `web-lego/` folder
3. Check for any new errors

### Step 3: Verify Installation
1. Open `debug.html` in the web-lego folder
2. Click all test buttons to verify functionality
3. Check Chrome DevTools console for any errors

## 🐛 Common Issues & Solutions

### Issue: Extension won't load
**Symptoms**: Error in Chrome extensions page
**Solutions**:
- Make sure all PNG icons are in `assets/` folder
- Check that `manifest.json` is valid JSON
- Verify all JavaScript files have no syntax errors

### Issue: Popup doesn't open
**Symptoms**: Nothing happens when clicking extension icon
**Solutions**:
- Check if popup.html exists and is valid
- Look for JavaScript errors in popup.js
- Try reloading the extension

### Issue: Content script not working
**Symptoms**: Can't select elements on webpages
**Solutions**:
- Check if contentScript.js loaded (use debug.html)
- Verify the website allows content scripts
- Try refreshing the webpage after activating

### Issue: Canvas not opening
**Symptoms**: "Canvas" button doesn't work
**Solutions**:
- Check browser console for errors
- Verify canvas.html and canvas.js are present
- Try disabling popup blockers

## 📋 File Checklist

Make sure these files exist in your `web-lego/` folder:

**Core Files:**
- ✅ `manifest.json`
- ✅ `popup.html`
- ✅ `popup.js`
- ✅ `contentScript.js`
- ✅ `canvas.html`
- ✅ `canvas.js`
- ✅ `background.js`
- ✅ `styles.css`

**Required Icons:**
- ✅ `assets/icon-16.png`
- ✅ `assets/icon-32.png`
- ✅ `assets/icon-48.png`
- ✅ `assets/icon-128.png`

**Helper Files:**
- ✅ `assets/create-png-icons.html`
- ✅ `debug.html`
- ✅ `README.md`
- ✅ `INSTALL.md`

## 🔍 Debug Steps

1. **Check Extension Status**:
   ```
   Go to chrome://extensions/
   Look for "Web Lego" extension
   Check if it's enabled
   Look for any error messages
   ```

2. **Test Basic Functionality**:
   ```
   Open debug.html in browser
   Run all tests
   Check console for errors
   ```

3. **Test on Simple Webpage**:
   ```
   Go to a simple website (like example.com)
   Click Web Lego extension icon
   Click "Activate Web Lego"
   Try selecting elements
   ```

## 💬 Still Having Issues?

If you're still experiencing problems:

1. **Check Chrome Version**: Make sure you're using Chrome 88+ (for Manifest V3 support)
2. **Try Incognito Mode**: Test the extension in incognito mode
3. **Reset Extension**: Remove and reinstall the extension completely
4. **Check Console**: Look for error messages in Chrome DevTools console

## 📝 Error Reporting

When reporting issues, please include:
- Chrome version
- Operating system
- Exact error message
- Steps to reproduce
- Screenshot of error (if applicable)

---

**The extension should now load without errors!** 🎉
