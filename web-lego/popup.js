// Popup script for Web Lego extension
// Handles activation button and communication with content script

document.addEventListener('DOMContentLoaded', function() {
    const activateBtn = document.getElementById('activateBtn');
    const demoBtn = document.getElementById('demoBtn');
    const status = document.getElementById('status');
    
    // Check if extension is already active on current tab
    checkExtensionStatus();
    
    // Handle demo button click
    demoBtn.addEventListener('click', function() {
        try {
            const demoUrl = chrome.runtime.getURL('demo-page.html');
            chrome.tabs.create({ url: demoUrl });
            window.close();
        } catch (error) {
            console.error('Error opening demo page:', error);
            showError('Could not open demo page');
        }
    });
    
    // Handle activation button click
    activateBtn.addEventListener('click', async function() {
        try {
            // Get current active tab
            const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
            
            if (!tab) {
                console.error('No active tab found');
                showError('No active tab found');
                return;
            }
            
            // Check if the current page allows content scripts
            if (!isValidUrl(tab.url)) {
                showError('Web Lego cannot run on this page. Try a regular website like google.com');
                return;
            }
            
            // Inject content script and activate Web Lego mode
            await chrome.scripting.executeScript({
                target: { tabId: tab.id },
                func: activateWebLego
            });
            
            // Update UI to show activated state
            showActivatedState();
            
            // Close popup after activation
            setTimeout(() => {
                window.close();
            }, 1500);
            
        } catch (error) {
            console.error('Error activating Web Lego:', error);
            
            // Provide more specific error messages
            if (error.message.includes('Cannot access')) {
                showError('Cannot access this page. Try a regular website.');
            } else if (error.message.includes('chrome://')) {
                showError('Web Lego cannot run on browser pages. Try a regular website.');
            } else {
                showError('Activation failed. Try refreshing the page.');
            }
        }
    });
    
    // Function to inject into content script context
    function activateWebLego() {
        // Check if Web Lego is already active
        if (window.webLegoActive) {
            return;
        }
        
        // Set active flag
        window.webLegoActive = true;
        
        // Dispatch custom event to activate Web Lego
        document.dispatchEvent(new CustomEvent('webLegoActivate'));
    }
    
    // Check if URL is valid for content script injection
    function isValidUrl(url) {
        if (!url) return false;
        
        // List of restricted URL patterns
        const restrictedPatterns = [
            'chrome://',
            'chrome-extension://',
            'moz-extension://',
            'edge://',
            'about:',
            'file://',
            'data:',
            'javascript:'
        ];
        
        // Check if URL starts with any restricted pattern
        return !restrictedPatterns.some(pattern => url.startsWith(pattern));
    }
    
    // Check current extension status
    async function checkExtensionStatus() {
        try {
            const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
            
            if (!tab) return;
            
            // Skip status check for restricted URLs
            if (!isValidUrl(tab.url)) {
                // Show info that extension can't run on this page
                status.textContent = 'Web Lego cannot run on this page. Try a regular website.';
                status.style.display = 'block';
                status.style.background = '#fef3c7';
                status.style.color = '#92400e';
                
                // Disable the activate button
                activateBtn.disabled = true;
                activateBtn.textContent = 'Not Available';
                activateBtn.style.opacity = '0.6';
                return;
            }
            
            // Check if Web Lego is already active
            const results = await chrome.scripting.executeScript({
                target: { tabId: tab.id },
                func: () => window.webLegoActive || false
            });
            
            if (results && results[0] && results[0].result) {
                showActivatedState();
            }
            
        } catch (error) {
            // Silently handle errors (might be on restricted pages)
            console.log('Could not check extension status:', error);
        }
    }
    
    // Show activated state UI
    function showActivatedState() {
        activateBtn.textContent = '✓ Web Lego Active';
        activateBtn.style.background = 'linear-gradient(135deg, #48bb78 0%, #38a169 100%)';
        status.classList.add('active');
    }
    
    // Show error state
    function showError(message = 'Error - Try Again') {
        activateBtn.textContent = message.length > 20 ? 'Error - Try Again' : message;
        activateBtn.style.background = 'linear-gradient(135deg, #f56565 0%, #e53e3e 100%)';
        
        // Show detailed message in status if it's long
        if (message.length > 20) {
            status.textContent = message;
            status.style.display = 'block';
            status.style.background = '#fed7d7';
            status.style.color = '#9b2c2c';
        }
        
        // Reset after 3 seconds
        setTimeout(() => {
            activateBtn.textContent = 'Activate Web Lego';
            activateBtn.style.background = 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)';
            status.style.display = 'none';
        }, 3000);
    }
});

// Handle messages from content script
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.type === 'webLegoStatus') {
        if (message.active) {
            showActivatedState();
        }
    }
});
