// Background service worker for Web Lego extension
// Handles extension lifecycle, storage management, and cross-tab communication

// Extension installation and update handling
chrome.runtime.onInstalled.addListener((details) => {
    console.log('Web Lego extension installed/updated:', details.reason);
    
    // Initialize storage on first install
    if (details.reason === 'install') {
        initializeExtension();
    }
    
    // Handle updates
    if (details.reason === 'update') {
        handleExtensionUpdate(details.previousVersion);
    }
});

// Initialize extension on first install
async function initializeExtension() {
    try {
        // Set default storage values
        await chrome.storage.local.set({
            webLegoBlocks: [],
            webLegoOnboardingShown: false,
            webLegoSettings: {
                autoSave: true,
                showNotifications: true,
                theme: 'light'
            }
        });
        
        console.log('Web Lego extension initialized successfully');
        
        // Show welcome notification
        showWelcomeNotification();
        
    } catch (error) {
        console.error('Error initializing Web Lego extension:', error);
    }
}

// Handle extension updates
async function handleExtensionUpdate(previousVersion) {
    try {
        console.log(`Web Lego updated from version ${previousVersion}`);
        
        // Perform any necessary data migrations here
        // For now, just log the update
        
    } catch (error) {
        console.error('Error handling extension update:', error);
    }
}

// Show welcome notification on first install
function showWelcomeNotification() {
    // Only show if notifications are supported
    if (chrome.notifications) {
        chrome.notifications.create('welcome', {
            type: 'basic',
            iconUrl: 'assets/icon-48.png',
            title: '🧱 Welcome to Web Lego!',
            message: 'Click the extension icon to start building with webpage elements!'
        });
    }
}

// Handle messages from content scripts and popup
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    console.log('Background received message:', message);
    
    switch (message.type) {
        case 'webLegoStatus':
            handleStatusUpdate(message, sender);
            break;
            
        case 'saveBlocks':
            handleSaveBlocks(message.blocks, sendResponse);
            return true; // Keep message channel open for async response
            
        case 'loadBlocks':
            handleLoadBlocks(sendResponse);
            return true; // Keep message channel open for async response
            
        case 'clearBlocks':
            handleClearBlocks(sendResponse);
            return true; // Keep message channel open for async response
            
        case 'getSettings':
            handleGetSettings(sendResponse);
            return true; // Keep message channel open for async response
            
        case 'updateSettings':
            handleUpdateSettings(message.settings, sendResponse);
            return true; // Keep message channel open for async response
            
        default:
            console.log('Unknown message type:', message.type);
    }
});

// Handle status updates from content script
function handleStatusUpdate(message, sender) {
    // Store the active state for the tab
    if (sender.tab) {
        // Could be used for tab-specific state management
        console.log(`Web Lego ${message.active ? 'activated' : 'deactivated'} on tab ${sender.tab.id}`);
    }
}

// Handle saving blocks
async function handleSaveBlocks(blocks, sendResponse) {
    try {
        await chrome.storage.local.set({ webLegoBlocks: blocks });
        sendResponse({ success: true });
    } catch (error) {
        console.error('Error saving blocks:', error);
        sendResponse({ success: false, error: error.message });
    }
}

// Handle loading blocks
async function handleLoadBlocks(sendResponse) {
    try {
        const result = await chrome.storage.local.get('webLegoBlocks');
        sendResponse({ 
            success: true, 
            blocks: result.webLegoBlocks || [] 
        });
    } catch (error) {
        console.error('Error loading blocks:', error);
        sendResponse({ success: false, error: error.message });
    }
}

// Handle clearing all blocks
async function handleClearBlocks(sendResponse) {
    try {
        await chrome.storage.local.set({ webLegoBlocks: [] });
        sendResponse({ success: true });
    } catch (error) {
        console.error('Error clearing blocks:', error);
        sendResponse({ success: false, error: error.message });
    }
}

// Handle getting settings
async function handleGetSettings(sendResponse) {
    try {
        const result = await chrome.storage.local.get('webLegoSettings');
        sendResponse({ 
            success: true, 
            settings: result.webLegoSettings || {
                autoSave: true,
                showNotifications: true,
                theme: 'light'
            }
        });
    } catch (error) {
        console.error('Error getting settings:', error);
        sendResponse({ success: false, error: error.message });
    }
}

// Handle updating settings
async function handleUpdateSettings(settings, sendResponse) {
    try {
        await chrome.storage.local.set({ webLegoSettings: settings });
        sendResponse({ success: true });
    } catch (error) {
        console.error('Error updating settings:', error);
        sendResponse({ success: false, error: error.message });
    }
}

// Handle storage changes and sync across tabs
chrome.storage.onChanged.addListener((changes, namespace) => {
    if (namespace === 'local') {
        // Notify all tabs about storage changes
        if (changes.webLegoBlocks) {
            notifyTabsOfBlocksChange(changes.webLegoBlocks);
        }
    }
});

// Notify all tabs about blocks changes
async function notifyTabsOfBlocksChange(blocksChange) {
    try {
        const tabs = await chrome.tabs.query({});
        
        tabs.forEach(tab => {
            // Send message to content script if it exists
            chrome.tabs.sendMessage(tab.id, {
                type: 'blocksChanged',
                blocks: blocksChange.newValue || []
            }).catch(() => {
                // Ignore errors for tabs without content script
            });
        });
        
    } catch (error) {
        console.error('Error notifying tabs of blocks change:', error);
    }
}

// Handle tab updates (when user navigates to new page)
chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
    // Reset Web Lego state when navigating to a new page
    if (changeInfo.status === 'complete' && tab.url) {
        // Could be used to reset extension state per tab
        console.log(`Tab ${tabId} loaded: ${tab.url}`);
    }
});

// Handle extension icon click (action)
chrome.action.onClicked.addListener(async (tab) => {
    // This won't be called if popup.html is set, but keeping for fallback
    try {
        await chrome.scripting.executeScript({
            target: { tabId: tab.id },
            func: () => {
                // Activate Web Lego if popup isn't working
                document.dispatchEvent(new CustomEvent('webLegoActivate'));
            }
        });
    } catch (error) {
        console.error('Error activating Web Lego via action click:', error);
    }
});

// Periodic cleanup of old data
setInterval(async () => {
    try {
        // Clean up old blocks (older than 30 days)
        const result = await chrome.storage.local.get('webLegoBlocks');
        const blocks = result.webLegoBlocks || [];
        
        const thirtyDaysAgo = Date.now() - (30 * 24 * 60 * 60 * 1000);
        const recentBlocks = blocks.filter(block => 
            block.timestamp && block.timestamp > thirtyDaysAgo
        );
        
        // Only update if we removed some blocks
        if (recentBlocks.length < blocks.length) {
            await chrome.storage.local.set({ webLegoBlocks: recentBlocks });
            console.log(`Cleaned up ${blocks.length - recentBlocks.length} old blocks`);
        }
        
    } catch (error) {
        console.error('Error during periodic cleanup:', error);
    }
}, 24 * 60 * 60 * 1000); // Run once per day

// Handle extension suspend/resume
chrome.runtime.onSuspend.addListener(() => {
    console.log('Web Lego extension suspending');
});

chrome.runtime.onStartup.addListener(() => {
    console.log('Web Lego extension starting up');
});

// Context menu setup (optional feature)
chrome.runtime.onInstalled.addListener(() => {
    // Create context menu for quick activation
    chrome.contextMenus.create({
        id: 'activateWebLego',
        title: '🧱 Activate Web Lego',
        contexts: ['page']
    });
});

// Handle context menu clicks
chrome.contextMenus.onClicked.addListener(async (info, tab) => {
    if (info.menuItemId === 'activateWebLego' && tab) {
        try {
            await chrome.scripting.executeScript({
                target: { tabId: tab.id },
                func: () => {
                    document.dispatchEvent(new CustomEvent('webLegoActivate'));
                }
            });
        } catch (error) {
            console.error('Error activating Web Lego via context menu:', error);
        }
    }
});

// Export functions for testing (if needed)
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        initializeExtension,
        handleExtensionUpdate,
        handleSaveBlocks,
        handleLoadBlocks,
        handleClearBlocks
    };
}
