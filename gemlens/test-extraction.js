// Simple test script to debug content extraction
// Run this in browser console on the Netflix page

console.log('=== GemLens Content Extraction Test ===');

// Test the extraction logic
function testExtraction() {
    const url = window.location.href;
    const title = document.title;
    
    console.log('URL:', url);
    console.log('Title:', title);
    
    let text = '';
    
    // Try to find main content areas
    const contentSelectors = [
        'article',
        'main', 
        '[role="main"]',
        '.content',
        '#content',
        '.post-content',
        '.entry-content'
    ];
    
    console.log('Testing content selectors...');
    
    for (const selector of contentSelectors) {
        const element = document.querySelector(selector);
        console.log(`Selector "${selector}":`, element ? 'FOUND' : 'NOT FOUND');
        if (element) {
            text = element.textContent || element.innerText || '';
            console.log(`Content length from ${selector}:`, text.length);
            console.log('Preview:', text.substring(0, 200) + '...');
            break;
        }
    }
    
    // Fallback to body content
    if (!text) {
        console.log('Using fallback: body content');
        const body = document.body.cloneNode(true);
        
        // Remove common non-content elements
        const removeSelectors = [
            'nav', 'header', 'footer', 'aside',
            '.navigation', '.nav', '.menu',
            '.sidebar', '.footer', '.header'
        ];
        
        removeSelectors.forEach(selector => {
            const elements = body.querySelectorAll(selector);
            console.log(`Removing ${elements.length} elements matching "${selector}"`);
            elements.forEach(el => el.remove());
        });
        
        text = body.textContent || body.innerText || '';
        console.log('Final body content length:', text.length);
    }
    
    // Clean up text
    text = text.replace(/\s+/g, ' ').trim();
    
    console.log('=== FINAL RESULT ===');
    console.log('Extracted text length:', text.length);
    console.log('First 500 characters:', text.substring(0, 500));
    
    return {
        text,
        title,
        url,
        type: window.location.hostname.includes('youtube.com') ? 'video' : 'webpage'
    };
}

// Run the test
const result = testExtraction();
console.log('Final extraction result:', result);
