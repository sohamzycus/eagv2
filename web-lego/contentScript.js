// Content script for Web Lego extension
// Handles element selection, hover effects, and toolbar injection

(function() {
    'use strict';
    
    // Global state
    let isWebLegoActive = false;
    let isSelectionMode = false;
    let selectedElements = [];
    let hoveredElement = null;
    let toolbar = null;
    let canvas = null;
    let onboardingOverlay = null;
    
    // Initialize Web Lego
    function initWebLego() {
        if (window.webLegoInitialized) return;
        window.webLegoInitialized = true;
        
        // Listen for activation event from popup
        document.addEventListener('webLegoActivate', activateWebLego);
        
        // Check if this is first time use
        checkFirstTimeUse();
    }
    
    // Activate Web Lego mode
    function activateWebLego() {
        if (isWebLegoActive) return;
        
        isWebLegoActive = true;
        window.webLegoActive = true;
        
        createToolbar();
        showOnboarding();
        
        // Notify popup of activation
        chrome.runtime.sendMessage({ type: 'webLegoStatus', active: true });
    }
    
    // Create floating toolbar
    function createToolbar() {
        if (toolbar) return;
        
        toolbar = document.createElement('div');
        toolbar.id = 'webLegoToolbar';
        toolbar.innerHTML = `
            <div class="web-lego-toolbar">
                <div class="toolbar-logo">🧱</div>
                <button id="selectBlocksBtn" class="toolbar-btn" title="Select Blocks">
                    <span class="btn-icon">🎯</span>
                    <span class="btn-text">Select</span>
                </button>
                <button id="addToCanvasBtn" class="toolbar-btn" title="Add Selected to Canvas" disabled>
                    <span class="btn-icon">➕</span>
                    <span class="btn-text">Add Selected</span>
                </button>
                <button id="addAllBtn" class="toolbar-btn" title="Add All Elements from Page">
                    <span class="btn-icon">📦</span>
                    <span class="btn-text">Add All</span>
                </button>
                <button id="openCanvasBtn" class="toolbar-btn" title="Open Canvas in New Tab">
                    <span class="btn-icon">🎨</span>
                    <span class="btn-text">Open Canvas</span>
                </button>
                <button id="closeWebLegoBtn" class="toolbar-btn close-btn" title="Close Web Lego">
                    <span class="btn-icon">✕</span>
                </button>
            </div>
        `;
        
        document.body.appendChild(toolbar);
        
        // Add event listeners
        setupToolbarEvents();
    }
    
    // Setup toolbar event listeners
    function setupToolbarEvents() {
        const selectBtn = document.getElementById('selectBlocksBtn');
        const addBtn = document.getElementById('addToCanvasBtn');
        const addAllBtn = document.getElementById('addAllBtn');
        const canvasBtn = document.getElementById('openCanvasBtn');
        const closeBtn = document.getElementById('closeWebLegoBtn');
        
        selectBtn.addEventListener('click', toggleSelectionMode);
        addBtn.addEventListener('click', addSelectedToCanvas);
        addAllBtn.addEventListener('click', addAllElementsToCanvas);
        canvasBtn.addEventListener('click', openCanvas);
        closeBtn.addEventListener('click', deactivateWebLego);
    }
    
    // Toggle element selection mode
    function toggleSelectionMode() {
        isSelectionMode = !isSelectionMode;
        const selectBtn = document.getElementById('selectBlocksBtn');
        
        if (isSelectionMode) {
            selectBtn.classList.add('active');
            selectBtn.innerHTML = `<span class="btn-icon">🛑</span><span class="btn-text">Stop</span>`;
            enableElementSelection();
        } else {
            selectBtn.classList.remove('active');
            selectBtn.innerHTML = `<span class="btn-icon">🎯</span><span class="btn-text">Select</span>`;
            disableElementSelection();
        }
    }
    
    // Enable element selection with hover effects
    function enableElementSelection() {
        document.addEventListener('mouseover', handleElementHover);
        document.addEventListener('mouseout', handleElementOut);
        document.addEventListener('click', handleElementClick);
        document.body.style.cursor = 'crosshair';
    }
    
    // Disable element selection
    function disableElementSelection() {
        document.removeEventListener('mouseover', handleElementHover);
        document.removeEventListener('mouseout', handleElementOut);
        document.removeEventListener('click', handleElementClick);
        document.body.style.cursor = '';
        
        // Remove hover effects
        if (hoveredElement) {
            hoveredElement.classList.remove('web-lego-hover');
            hoveredElement = null;
        }
    }
    
    // Handle element hover
    function handleElementHover(e) {
        if (!isSelectionMode) return;
        
        const element = e.target;
        
        // Skip toolbar and canvas elements
        if (element.closest('#webLegoToolbar') || element.closest('#webLegoCanvas')) {
            return;
        }
        
        // Skip already selected elements
        if (selectedElements.includes(element)) return;
        
        // Remove previous hover effect
        if (hoveredElement && hoveredElement !== element) {
            hoveredElement.classList.remove('web-lego-hover');
        }
        
        // Add hover effect to current element
        element.classList.add('web-lego-hover');
        hoveredElement = element;
    }
    
    // Handle element mouse out
    function handleElementOut(e) {
        if (!isSelectionMode) return;
        
        const element = e.target;
        if (element === hoveredElement && !selectedElements.includes(element)) {
            element.classList.remove('web-lego-hover');
        }
    }
    
    // Handle element click for selection
    function handleElementClick(e) {
        if (!isSelectionMode) return;
        
        e.preventDefault();
        e.stopPropagation();
        
        const element = e.target;
        
        // Skip toolbar and canvas elements
        if (element.closest('#webLegoToolbar') || element.closest('#webLegoCanvas')) {
            return;
        }
        
        // Toggle selection
        if (selectedElements.includes(element)) {
            // Deselect
            selectedElements = selectedElements.filter(el => el !== element);
            element.classList.remove('web-lego-selected');
        } else {
            // Select
            selectedElements.push(element);
            element.classList.add('web-lego-selected');
            element.classList.remove('web-lego-hover');
        }
        
        // Update add button state
        updateAddButtonState();
    }
    
    // Update add button state
    function updateAddButtonState() {
        const addBtn = document.getElementById('addToCanvasBtn');
        if (selectedElements.length > 0) {
            addBtn.disabled = false;
            addBtn.classList.add('has-selection');
        } else {
            addBtn.disabled = true;
            addBtn.classList.remove('has-selection');
        }
    }
    
    // Add selected elements to canvas
    async function addSelectedToCanvas() {
        if (selectedElements.length === 0) return;
        
        const blocks = [];
        
        // Extract content from selected elements
        selectedElements.forEach((element, index) => {
            const block = extractElementContent(element, index);
            if (block) {
                blocks.push(block);
            }
        });
        
        // Store blocks in chrome storage
        try {
            const existingBlocks = await getStoredBlocks();
            const allBlocks = [...existingBlocks, ...blocks];
            
            await chrome.storage.local.set({ webLegoBlocks: allBlocks });
            
            // Clear selections
            clearSelections();
            
            // Show success feedback
            showNotification(`Added ${blocks.length} block(s) to canvas!`);
            
            // Open canvas
            openCanvas();
            
        } catch (error) {
            console.error('Error saving blocks:', error);
            showNotification('Could not save blocks. Try reloading the extension.');
        }
    }
    
    // Add all suitable elements from page to canvas
    async function addAllElementsToCanvas() {
        // Find all suitable elements (divs, sections, articles, headers, etc.)
        const allElements = document.querySelectorAll(
            'div, section, article, header, main, aside, footer, p, h1, h2, h3, h4, h5, h6, blockquote, img, video, figure, nav'
        );
        
        const suitableElements = [];
        
        allElements.forEach(element => {
            // Skip toolbar, canvas, and other extension elements
            if (element.closest('#webLegoToolbar') || 
                element.closest('#webLegoCanvas') || 
                element.closest('#webLegoOnboarding')) {
                return;
            }
            
            // Skip elements that are too small or hidden
            const rect = element.getBoundingClientRect();
            if (rect.width < 50 || rect.height < 20 || rect.width === 0 || rect.height === 0) {
                return;
            }
            
            // Skip elements that are mostly empty
            const text = element.textContent.trim();
            const hasContent = text.length > 5 || 
                              element.querySelector('img, video, canvas, svg') ||
                              element.style.backgroundImage;
            
            if (hasContent) {
                suitableElements.push(element);
            }
        });
        
        // Limit to prevent overwhelming the canvas
        const elementsToAdd = suitableElements.slice(0, 20);
        
        if (elementsToAdd.length === 0) {
            showNotification('No suitable elements found on this page');
            return;
        }
        
        const blocks = [];
        
        // Extract content from all suitable elements
        elementsToAdd.forEach((element, index) => {
            const block = extractElementContent(element, index);
            if (block) {
                // Spread them out more for "Add All"
                block.x = 50 + (index % 4) * 250;
                block.y = 50 + Math.floor(index / 4) * 200;
                blocks.push(block);
            }
        });
        
        // Store blocks in chrome storage
        try {
            const existingBlocks = await getStoredBlocks();
            const allBlocks = [...existingBlocks, ...blocks];
            
            await chrome.storage.local.set({ webLegoBlocks: allBlocks });
            
            // Show success feedback
            showNotification(`Added ${blocks.length} elements from this page!`);
            
            // Open canvas
            openCanvas();
            
        } catch (error) {
            console.error('Error saving blocks:', error);
            showNotification('Could not save blocks. Try reloading the extension.');
        }
    }
    
    // Extract content from DOM element
    function extractElementContent(element, index) {
        const rect = element.getBoundingClientRect();
        
        // Get computed styles
        const computedStyle = window.getComputedStyle(element);
        
        // Clone element to preserve styling
        const clonedElement = element.cloneNode(true);
        
        // Remove any Web Lego classes
        clonedElement.classList.remove('web-lego-hover', 'web-lego-selected');
        
        return {
            id: `block-${Date.now()}-${index}`,
            content: clonedElement.outerHTML,
            type: element.tagName.toLowerCase(),
            width: Math.max(200, Math.min(400, rect.width)),
            height: Math.max(100, Math.min(300, rect.height)),
            x: 50 + (index * 20),
            y: 50 + (index * 20),
            timestamp: Date.now(),
            editable: true,  // Make all webpage blocks editable
            source: 'webpage'  // Track source for better handling
        };
    }
    
    // Get stored blocks from chrome storage
    async function getStoredBlocks() {
        try {
            const result = await chrome.storage.local.get('webLegoBlocks');
            return result.webLegoBlocks || [];
        } catch (error) {
            console.error('Error getting stored blocks:', error);
            return [];
        }
    }
    
    // Clear all selections
    function clearSelections() {
        selectedElements.forEach(element => {
            element.classList.remove('web-lego-selected');
        });
        selectedElements = [];
        updateAddButtonState();
    }
    
    // Open canvas in new tab
    function openCanvas() {
        try {
            const canvasUrl = chrome.runtime.getURL('canvas.html');
            window.open(canvasUrl, '_blank', 'width=1200,height=800,scrollbars=yes,resizable=yes');
            showNotification('Canvas opened in new tab!');
        } catch (error) {
            console.error('Error opening canvas:', error);
            openCanvasModal();
        }
    }
    
    // Fallback: Open canvas as full-screen modal overlay
    function openCanvasModal() {
        if (canvas) {
            canvas.style.display = 'block';
            return;
        }
        
        try {
            const canvasUrl = chrome.runtime.getURL('canvas.html');
            
            canvas = document.createElement('div');
            canvas.id = 'webLegoCanvas';
            canvas.innerHTML = `
                <div style="position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; background: white; z-index: 999999; display: flex; flex-direction: column;">
                    <div style="height: 50px; background: #667eea; color: white; display: flex; align-items: center; justify-content: space-between; padding: 0 20px;">
                        <div style="font-weight: 600;">🧱 Web Lego Canvas</div>
                        <button onclick="this.closest('#webLegoCanvas').remove()" style="background: rgba(255,255,255,0.2); border: none; color: white; padding: 8px 12px; border-radius: 6px; cursor: pointer;">✕ Close</button>
                    </div>
                    <iframe src="${canvasUrl}" 
                            frameborder="0" 
                            style="flex: 1; width: 100%; border: none;">
                    </iframe>
                </div>
            `;
            
            document.body.appendChild(canvas);
            showNotification('Canvas opened in modal');
        } catch (error) {
            console.error('Cannot open canvas modal:', error);
            showNotification('Cannot open canvas. Please reload the page and try again.');
        }
    }
    
    // Show notification
    function showNotification(message) {
        const notification = document.createElement('div');
        notification.className = 'web-lego-notification';
        notification.textContent = message;
        
        document.body.appendChild(notification);
        
        // Auto-remove after 3 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 3000);
    }
    
    // Show onboarding overlay
    function showOnboarding() {
        try {
            chrome.storage.local.get('webLegoOnboardingShown').then(result => {
                if (!result.webLegoOnboardingShown) {
                    createOnboardingOverlay();
                }
            }).catch(error => {
                console.log('Error checking onboarding status:', error);
            });
        } catch (error) {
            console.log('Error accessing storage for onboarding check:', error);
        }
    }
    
    // Create onboarding overlay
    function createOnboardingOverlay() {
        onboardingOverlay = document.createElement('div');
        onboardingOverlay.id = 'webLegoOnboarding';
        onboardingOverlay.innerHTML = `
            <div class="onboarding-overlay">
                <div class="onboarding-content">
                    <h2>🧱 Welcome to Web Lego!</h2>
                    <div class="onboarding-steps">
                        <div class="step">
                            <div class="step-number">1</div>
                            <div class="step-text">Click "Select" and hover over elements to highlight them</div>
                        </div>
                        <div class="step">
                            <div class="step-number">2</div>
                            <div class="step-text">Click elements to select them (they'll turn blue)</div>
                        </div>
                        <div class="step">
                            <div class="step-number">3</div>
                            <div class="step-text">Click "Add" to move them to your canvas</div>
                        </div>
                        <div class="step">
                            <div class="step-number">4</div>
                            <div class="step-text">Open "Canvas" to arrange and remix your blocks!</div>
                        </div>
                    </div>
                    <button id="startOnboardingBtn" class="onboarding-btn">Got it! Let's start</button>
                    <button id="skipOnboardingBtn" class="onboarding-btn secondary">Skip tour</button>
                </div>
            </div>
        `;
        
        document.body.appendChild(onboardingOverlay);
        
        // Setup onboarding events
        document.getElementById('startOnboardingBtn').addEventListener('click', startOnboarding);
        document.getElementById('skipOnboardingBtn').addEventListener('click', skipOnboarding);
    }
    
    // Start onboarding process
    function startOnboarding() {
        // Mark onboarding as shown
        try {
            chrome.storage.local.set({ webLegoOnboardingShown: true });
        } catch (error) {
            console.log('Could not save onboarding status:', error);
        }
        
        // Remove overlay
        if (onboardingOverlay) {
            onboardingOverlay.remove();
            onboardingOverlay = null;
        }
        
        // Create demo blocks if no content selected
        createDemoBlocks();
        
        // Auto-activate selection mode
        setTimeout(() => {
            if (!isSelectionMode) {
                toggleSelectionMode();
            }
        }, 500);
    }
    
    // Skip onboarding
    function skipOnboarding() {
        try {
            chrome.storage.local.set({ webLegoOnboardingShown: true });
        } catch (error) {
            console.log('Could not save onboarding status:', error);
        }
        
        if (onboardingOverlay) {
            onboardingOverlay.remove();
            onboardingOverlay = null;
        }
    }
    
    // Create demo blocks for first-time users
    async function createDemoBlocks() {
        const demoBlocks = [
            {
                id: 'demo-text-1',
                content: '<div style="padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border-radius: 12px; font-family: -apple-system, BlinkMacSystemFont, \'Segoe UI\', sans-serif;"><h3 style="margin: 0 0 10px;">Welcome to Web Lego! 🧱</h3><p style="margin: 0; opacity: 0.9;">This is a demo text block. Try dragging it around!</p></div>',
                type: 'div',
                width: 300,
                height: 120,
                x: 50,
                y: 50,
                timestamp: Date.now(),
                editable: true
            },
            {
                id: 'demo-quote-1',
                content: '<blockquote style="margin: 0; padding: 20px; background: #f7fafc; border-left: 4px solid #4299e1; border-radius: 8px; font-style: italic; color: #2d3748;"><p style="margin: 0;">"The best way to predict the future is to invent it."</p><footer style="margin-top: 10px; font-size: 14px; color: #718096;">— Alan Kay</footer></blockquote>',
                type: 'blockquote',
                width: 350,
                height: 100,
                x: 80,
                y: 200,
                timestamp: Date.now() + 1,
                editable: true
            },
            {
                id: 'demo-image-1',
                content: '<div style="padding: 15px; background: white; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.1);"><div style="width: 200px; height: 120px; background: linear-gradient(45deg, #ff6b6b, #4ecdc4); border-radius: 8px; display: flex; align-items: center; justify-content: center; color: white; font-size: 18px; font-weight: bold;">📸 Demo Image</div><p style="margin: 10px 0 0; font-size: 14px; color: #666; text-align: center;">Drag me around!</p></div>',
                type: 'div',
                width: 230,
                height: 180,
                x: 110,
                y: 330,
                timestamp: Date.now() + 2,
                editable: true
            }
        ];
        
        try {
            await chrome.storage.local.set({ webLegoBlocks: demoBlocks });
        } catch (error) {
            console.log('Error creating demo blocks:', error);
        }
    }
    
    // Check if this is first time use
    function checkFirstTimeUse() {
        try {
            chrome.storage.local.get('webLegoOnboardingShown').then(result => {
                if (!result.webLegoOnboardingShown) {
                    // This is first time use, we'll show onboarding when activated
                }
            }).catch(error => {
                console.log('Error checking first time use:', error);
            });
        } catch (error) {
            console.log('Error accessing storage for first time check:', error);
        }
    }
    
    // Deactivate Web Lego
    function deactivateWebLego() {
        isWebLegoActive = false;
        window.webLegoActive = false;
        
        // Disable selection mode
        if (isSelectionMode) {
            toggleSelectionMode();
        }
        
        // Clear selections
        clearSelections();
        
        // Remove toolbar
        if (toolbar) {
            toolbar.remove();
            toolbar = null;
        }
        
        // Hide canvas
        if (canvas) {
            canvas.style.display = 'none';
        }
        
        // Remove onboarding if present
        if (onboardingOverlay) {
            onboardingOverlay.remove();
            onboardingOverlay = null;
        }
    }
    
    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initWebLego);
    } else {
        initWebLego();
    }
    
})();
