// Simple icon generator for Web Lego extension
// Creates basic PNG icons using Canvas API (requires Node.js with canvas support)

const fs = require('fs');

// Simple PNG header for a minimal icon
function createSimplePNG(size, color) {
    // This is a very basic approach - in practice, you'd use a proper image library
    // For now, we'll create a simple colored square with rounded corners
    
    const canvas = `
    <svg width="${size}" height="${size}" xmlns="http://www.w3.org/2000/svg">
        <defs>
            <linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" style="stop-color:#667eea"/>
                <stop offset="100%" style="stop-color:#764ba2"/>
            </linearGradient>
        </defs>
        <rect width="${size}" height="${size}" rx="${size * 0.2}" fill="url(#bg)"/>
        <rect x="${size * 0.1}" y="${size * 0.2}" width="${size * 0.35}" height="${size * 0.25}" rx="${size * 0.05}" fill="#ff6b6b"/>
        <rect x="${size * 0.55}" y="${size * 0.15}" width="${size * 0.3}" height="${size * 0.2}" rx="${size * 0.04}" fill="#4ecdc4"/>
        <rect x="${size * 0.25}" y="${size * 0.55}" width="${size * 0.25}" height="${size * 0.15}" rx="${size * 0.03}" fill="#45b7d1"/>
        <rect x="${size * 0.6}" y="${size * 0.6}" width="${size * 0.2}" height="${size * 0.12}" rx="${size * 0.02}" fill="#96ceb4"/>
        <text x="${size/2}" y="${size * 0.85}" text-anchor="middle" font-family="Arial" font-size="${size * 0.15}" fill="white">🧱</text>
    </svg>`;
    
    return canvas;
}

// Generate SVG icons for different sizes
const sizes = [16, 32, 48, 128];

sizes.forEach(size => {
    const svg = createSimplePNG(size);
    fs.writeFileSync(`icon-${size}.svg`, svg);
    console.log(`Generated icon-${size}.svg`);
});

console.log('\nSVG icons generated! To convert to PNG:');
console.log('1. Use the create-icons.html file in a browser, OR');
console.log('2. Use an online SVG to PNG converter, OR');
console.log('3. Use ImageMagick: magick icon-16.svg icon-16.png');
console.log('\nThe extension will work with SVG files as well if PNG conversion is not available.');
