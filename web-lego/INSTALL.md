# 🚀 Web Lego Extension - Installation Guide

## Quick Installation (3 Steps)

### Step 1: Generate Icons
1. Open `assets/create-png-icons.html` in any web browser
2. The page will automatically download 4 PNG files
3. Save all downloaded files to the `assets/` folder:
   - `icon-16.png`
   - `icon-32.png` 
   - `icon-48.png`
   - `icon-128.png`

### Step 2: Load Extension in Chrome
1. Open Chrome and go to `chrome://extensions/`
2. Toggle **"Developer mode"** ON (top-right corner)
3. Click **"Load unpacked"**
4. Select this `web-lego/` folder
5. The extension should appear in your extensions list

### Step 3: Pin & Use
1. Pin the Web Lego extension to your toolbar
2. Visit any webpage
3. Click the extension icon and press **"Activate Web Lego"**
4. Start selecting elements and building!

## ✅ Verification

If everything worked correctly, you should see:
- ✅ Web Lego extension in Chrome extensions list
- ✅ Colorful Lego block icon in toolbar
- ✅ No error messages
- ✅ Popup opens when clicking the icon

## 🐛 Troubleshooting

**Extension won't load?**
- Make sure all 4 PNG icon files are in the `assets/` folder
- Check that you selected the `web-lego/` folder (not the parent folder)

**Icons appear broken?**
- Re-run Step 1 to generate PNG icons
- Verify all 4 PNG files are correctly named and in `assets/`

**Can't activate on websites?**
- Try refreshing the webpage
- Some sites (like chrome:// pages) don't allow extensions

## 📁 Required Files Checklist

Your `web-lego/` folder should contain:
- ✅ `manifest.json`
- ✅ `popup.html` + `popup.js`
- ✅ `contentScript.js`
- ✅ `canvas.html` + `canvas.js`
- ✅ `background.js`
- ✅ `styles.css`
- ✅ `assets/icon-16.png`
- ✅ `assets/icon-32.png`
- ✅ `assets/icon-48.png`
- ✅ `assets/icon-128.png`

---

**🎉 Ready to build with Web Lego!**
