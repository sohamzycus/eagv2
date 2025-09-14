import { ExtractedContent } from '../shared/types';
import { isYouTubePage, extractTextFromHtml } from '../shared/utils';

/**
 * Content script for extracting page content and handling overlay injection
 */

class PageExtractor {
  /**
   * Extract main content from the current page
   */
  extractPageContent(): ExtractedContent {
    const url = window.location.href;
    const title = document.title;
    
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
    
    for (const selector of contentSelectors) {
      const element = document.querySelector(selector);
      if (element) {
        text = extractTextFromHtml(element.innerHTML);
        break;
      }
    }
    
    // Fallback to body content, but filter out navigation and footer
    if (!text) {
      const body = document.body.cloneNode(true) as HTMLElement;
      
      // Remove common non-content elements
      const removeSelectors = [
        'nav', 'header', 'footer', 'aside',
        '.navigation', '.nav', '.menu',
        '.sidebar', '.footer', '.header'
      ];
      
      removeSelectors.forEach(selector => {
        const elements = body.querySelectorAll(selector);
        elements.forEach(el => el.remove());
      });
      
      text = extractTextFromHtml(body.innerHTML);
    }
    
    // Clean up text
    text = text.replace(/\s+/g, ' ').trim();
    
    const result: ExtractedContent = {
      text,
      title,
      url,
      type: 'webpage'
    };
    
    // Try to extract YouTube captions if on YouTube
    if (isYouTubePage()) {
      result.type = 'video';
      result.captions = this.extractYouTubeCaptions();
    }
    
    return result;
  }
  
  /**
   * Attempt to extract YouTube captions/transcript
   */
  private extractYouTubeCaptions(): string | undefined {
    try {
      // Method 1: Try to find transcript renderer
      const transcriptRenderer = document.querySelector('ytd-transcript-renderer');
      if (transcriptRenderer) {
        const segments = transcriptRenderer.querySelectorAll('.segment-text');
        return Array.from(segments).map(seg => seg.textContent).join(' ');
      }
      
      // Method 2: Try to access ytInitialPlayerResponse
      const scripts = document.querySelectorAll('script');
      for (const script of scripts) {
        const content = script.textContent || '';
        if (content.includes('ytInitialPlayerResponse')) {
          const match = content.match(/ytInitialPlayerResponse\s*=\s*({.+?});/);
          if (match) {
            try {
              const playerResponse = JSON.parse(match[1]);
              const captions = playerResponse?.captions?.playerCaptionsTracklistRenderer?.captionTracks;
              if (captions && captions.length > 0) {
                // Return indication that captions are available
                return 'Captions available but require additional processing';
              }
            } catch (e) {
              console.warn('Failed to parse ytInitialPlayerResponse', e);
            }
          }
        }
      }
    } catch (error) {
      console.warn('Failed to extract YouTube captions', error);
    }
    
    return undefined;
  }
}

const extractor = new PageExtractor();

// Listen for messages from popup/background
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.action === 'extractContent') {
    try {
      const content = extractor.extractPageContent();
      sendResponse({ success: true, content });
    } catch (error) {
      sendResponse({ success: false, error: (error as Error).message });
    }
    return true;
  }
  
  if (message.action === 'showOverlay') {
    showGeminiOverlay();
    sendResponse({ success: true });
    return true;
  }
});

/**
 * Show the Gemini chat overlay
 */
function showGeminiOverlay() {
  // Check if overlay already exists
  if (document.getElementById('gemlens-overlay')) {
    return;
  }
  
  // Create overlay iframe
  const overlay = document.createElement('iframe');
  overlay.id = 'gemlens-overlay';
  overlay.src = chrome.runtime.getURL('content/overlay/overlay.html');
  overlay.style.cssText = `
    position: fixed;
    top: 20px;
    right: 20px;
    width: 400px;
    height: 600px;
    border: none;
    border-radius: 12px;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
    z-index: 10000;
    background: white;
  `;
  
  document.body.appendChild(overlay);
}

// Initialize content script
console.log('GemLens content script loaded');
