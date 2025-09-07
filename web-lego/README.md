# 🧱 Web Lego - Modular Page Composer

**A Chrome Extension that lets you pick pieces of any webpage and rearrange them in a clean canvas UI. Think of it as Lego for the web – modular, intuitive, and visual.**

## ✨ Features

### 🎯 Element Selection & Creation
- **Webpage Selection**: Hover and click to select any webpage element
- **Built-in Tools**: Add text blocks, images, and shapes directly
- **Smart Selection**: Intelligent element detection and extraction

### 🎨 Advanced Canvas Studio
- **Professional Layout**: Wide canvas with sidebar tools and instructions
- **Live Editing**: Double-click any block to edit text content
- **Complex Layouts**: Overlap blocks, create layered compositions
- **Drag & Drop**: Smooth dragging with visual feedback
- **Precise Resizing**: Drag corner handles to resize blocks

### 💡 User-Friendly Design
- **Guided Interface**: Step-by-step instructions in sidebar
- **Visual Stats**: See block count and layout complexity
- **Selection Tools**: Click blocks to select, use keyboard shortcuts
- **Undo/Redo**: Full history management with keyboard shortcuts

### 📤 Export & Sharing
- **HTML Export**: Download complete HTML files
- **Share Links**: Create shareable URLs of your layouts
- **Code Export**: Copy HTML/CSS code for your layouts
- **Templates**: Save layouts as reusable templates
- **Image Export**: Export as PNG/JPEG (coming soon)

### 🚀 Pro Features
- **Zoom Controls**: Zoom in/out and fit to screen
- **Keyboard Shortcuts**: Ctrl+Z/Y for undo/redo, Delete to remove blocks
- **Auto-Save**: Your work is automatically saved
- **Offline Mode**: Works even when extension context is invalidated
- **Block Duplication**: Easily duplicate blocks with one click

## 🚀 Installation

### Method 1: Load Unpacked (Recommended for Development)

1. **Download/Clone** this repository
2. **Generate Icons**: Open `assets/create-png-icons.html` in your browser and download all 4 PNG icons to the `assets/` folder
3. **Open Chrome** and navigate to `chrome://extensions/`
4. **Enable Developer Mode** (toggle in top-right)
5. **Click "Load unpacked"** and select this extension folder
6. **Pin the Extension** to your toolbar for easy access

### Method 2: Generate Icons First (If Method 1 doesn't work)

If you see icon errors, generate PNG icons first:

```bash
# Option A: Use the browser-based generator
open assets/create-png-icons.html

# Option B: Use ImageMagick (if installed)
cd assets
magick icon.svg -resize 16x16 icon-16.png
magick icon.svg -resize 32x32 icon-32.png  
magick icon.svg -resize 48x48 icon-48.png
magick icon.svg -resize 128x128 icon-128.png
```

## 🎮 How to Use

1. **Activate**: Click the Web Lego extension icon and press "Activate Web Lego"
2. **Select Elements**: 
   - Click "Select" in the floating toolbar
   - Hover over webpage elements to highlight them
   - Click elements to select them (they turn green with a checkmark)
3. **Add to Canvas**: Click "Add" to move selected elements to your canvas
4. **Arrange**: Click "Open Canvas" to launch the full-screen workspace where you can:
   - Drag blocks around
   - Resize blocks by dragging the corner
   - Delete blocks with the × button
5. **Save**: Your layout is automatically saved!

## 📁 File Structure

```
web-lego-extension/
├── manifest.json          # Extension configuration
├── popup.html             # Extension popup UI
├── popup.js               # Popup functionality
├── contentScript.js       # Page element selection
├── canvas.html            # Drag & drop workspace
├── canvas.js              # Canvas functionality
├── background.js          # Service worker
├── styles.css             # Modern UI styles
├── assets/                # Icons and resources
│   ├── icon.svg          # Master icon file
│   ├── icon-*.png        # Required PNG icons (16,32,48,128px)
│   ├── create-png-icons.html # Icon generator
│   └── README.md         # Icon documentation
└── README.md             # This file
```

## 🛠️ Technical Details

- **Manifest Version**: 3 (latest Chrome extension format)
- **Permissions**: `activeTab`, `scripting`, `storage`
- **Storage**: Uses `chrome.storage.local` for persistence
- **Framework**: Vanilla JavaScript (no dependencies)
- **Styling**: Modern CSS with animations and responsive design
- **Icons**: Colorful Lego-block style design

## 🎨 Design Philosophy

- **Minimalist**: Clean, uncluttered interface
- **Intuitive**: No learning curve required
- **Responsive**: Works on all screen sizes
- **Accessible**: High contrast support, reduced motion support
- **Modern**: Gradients, rounded corners, smooth animations

## 🐛 Troubleshooting

### Extension won't load
- Make sure all PNG icon files are present in `assets/` folder
- Check Chrome Developer Console for errors
- Try reloading the extension

### Can't select elements
- Make sure Web Lego is activated (green button in popup)
- Try refreshing the page and reactivating
- Check if the page allows content scripts

### Canvas not opening
- Disable popup blockers
- Try clicking "Canvas" button again
- Check browser console for errors

### Icons appear broken
- Generate PNG icons using `assets/create-png-icons.html`
- Ensure all 4 PNG files are correctly named and sized

## 🚀 Development

### Adding New Features

1. **Content Script** (`contentScript.js`): For webpage interaction
2. **Canvas** (`canvas.js`): For workspace functionality  
3. **Background** (`background.js`): For extension lifecycle
4. **Styles** (`styles.css`): For UI improvements

### Testing

1. Load extension in Chrome Developer Mode
2. Test on various websites
3. Check console for errors
4. Verify storage persistence

## 📄 License

This project is open source. Feel free to modify and distribute.

## 🤝 Contributing

Contributions welcome! Please feel free to submit pull requests or open issues.

---

**Built with ❤️ for creative web users who want to remix the internet!**