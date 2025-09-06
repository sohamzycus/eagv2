# Web Lego Extension Icons

## 🎨 Icon Generation

This folder contains the icon assets for the Web Lego Chrome extension.

### Quick Setup (Recommended)

1. **Open the Icon Generator**: Open `create-icons.html` in any web browser
2. **Download Icons**: Click each "Download" button to save the PNG files
3. **Save to Assets**: Place all downloaded PNG files in this `assets/` folder

The required icon files are:
- `icon-16.png` (16x16 pixels)
- `icon-32.png` (32x32 pixels) 
- `icon-48.png` (48x48 pixels)
- `icon-128.png` (128x128 pixels)

### Alternative Methods

#### Method 1: Using Online Converters
1. Upload `icon.svg` to any SVG-to-PNG converter (like CloudConvert, Convertio, etc.)
2. Generate PNG files at sizes: 16px, 32px, 48px, and 128px
3. Name them as listed above and save to this folder

#### Method 2: Using Command Line (if you have ImageMagick installed)
```bash
# Convert SVG to different PNG sizes
magick icon.svg -resize 16x16 icon-16.png
magick icon.svg -resize 32x32 icon-32.png
magick icon.svg -resize 48x48 icon-48.png
magick icon.svg -resize 128x128 icon-128.png
```

#### Method 3: Using Node.js (if you have sharp installed)
```bash
npm install sharp
node -e "
const sharp = require('sharp');
const svg = require('fs').readFileSync('icon.svg');
[16,32,48,128].forEach(size => {
  sharp(svg).resize(size, size).png().toFile(\`icon-\${size}.png\`);
});
"
```

## 🧱 Icon Design

The Web Lego icon features:
- **Colorful Lego blocks** in a modern, flat design
- **Gradient backgrounds** for depth and visual appeal
- **White studs** on each block for authentic Lego look
- **Multiple sizes** optimized for different UI contexts

The color palette includes:
- Primary: `#667eea` to `#764ba2` (purple gradient)
- Block colors: `#ff6b6b` (red), `#4ecdc4` (teal), `#45b7d1` (blue), `#96ceb4` (green)

## 📁 File Structure

```
assets/
├── icon.svg              # Master SVG icon
├── icon-16.png          # 16x16 PNG (toolbar)
├── icon-32.png          # 32x32 PNG (menu)
├── icon-48.png          # 48x48 PNG (extension management)
├── icon-128.png         # 128x128 PNG (Chrome Web Store)
├── create-icons.html    # Icon generator tool
└── README.md           # This file
```

## ✅ Verification

After generating the icons, verify that:
1. All 4 PNG files are present in the assets folder
2. Each file has the correct dimensions
3. The extension loads without icon errors in Chrome Developer Mode

If you see broken icon images in Chrome, double-check that all PNG files are properly generated and named correctly.
