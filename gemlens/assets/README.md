# GemLens Assets

This folder contains the visual assets for the GemLens Chrome Extension.

## Files

- `logo.svg` - Main SVG logo used throughout the extension
- `create-icons.html` - Tool to generate PNG icons from the SVG
- `icon16.png` - 16x16 icon for browser toolbar (generated)
- `icon48.png` - 48x48 icon for extension management (generated)
- `icon128.png` - 128x128 icon for Chrome Web Store (generated)

## Generating PNG Icons

1. Open `create-icons.html` in your browser
2. Click "Generate Icons" to create PNG versions from the SVG
3. Click "Download All Icons" or right-click each icon to save
4. Save them as `icon16.png`, `icon48.png`, and `icon128.png` in this folder

## Icon Design

The GemLens logo combines:
- **Gem shape**: Represents the "Gem" in Gemini AI
- **Magnifying glass**: Represents the "Lens" for analysis
- **Gradient colors**: Modern purple-blue gradient
- **Sparkle effects**: AI magic and intelligence
- **Brain pattern**: Subtle AI/neural network reference

## Usage in Extension

The icons are referenced in `manifest.json`:

```json
{
  "action": {
    "default_icon": {
      "16": "assets/icon16.png",
      "48": "assets/icon48.png", 
      "128": "assets/icon128.png"
    }
  },
  "icons": {
    "16": "assets/icon16.png",
    "48": "assets/icon48.png",
    "128": "assets/icon128.png"
  }
}
```

## Design Guidelines

- **Colors**: Use the gradient from #667eea to #764ba2 for primary elements
- **Accent**: Use #f093fb to #f5576c for secondary elements (lens)
- **Style**: Modern, clean, professional
- **Scalability**: Icons should be readable at 16x16 pixels
- **Consistency**: Maintain the same visual style across all sizes
