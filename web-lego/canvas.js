// Enhanced Canvas script for Web Lego extension
// Handles advanced block editing, layouts, and export features

(function() {
    'use strict';
    
    // Global state
    let blocks = [];
    let selectedBlock = null;
    let draggedBlock = null;
    let dragOffset = { x: 0, y: 0 };
    let resizingBlock = null;
    let resizeStartPos = { x: 0, y: 0 };
    let resizeStartSize = { width: 0, height: 0 };
    let history = [];
    let historyIndex = -1;
    let zoom = 1;
    let nextBlockId = 1;
    
    // DOM elements
    const workspace = document.getElementById('workspace');
    const emptyState = document.getElementById('emptyState');
    const blockCount = document.getElementById('blockCount');
    const layerCount = document.getElementById('layerCount');
    
    // Toolbar buttons
    const addTextBtn = document.getElementById('addTextBtn');
    const addImageBtn = document.getElementById('addImageBtn');
    const addShapeBtn = document.getElementById('addShapeBtn');
    const selectModeBtn = document.getElementById('selectModeBtn');
    const exportBtn = document.getElementById('exportBtn');
    const saveTemplateBtn = document.getElementById('saveTemplateBtn');
    const resetBtn = document.getElementById('resetBtn');
    const getDemoBlocksBtn = document.getElementById('getDemoBlocks');
    const openTutorialBtn = document.getElementById('openTutorial');
    
    // Canvas controls
    const undoBtn = document.getElementById('undoBtn');
    const redoBtn = document.getElementById('redoBtn');
    const zoomInBtn = document.getElementById('zoomInBtn');
    const zoomOutBtn = document.getElementById('zoomOutBtn');
    const fitToScreenBtn = document.getElementById('fitToScreenBtn');
    
    // Initialize canvas
    function initCanvas() {
        loadBlocks();
        setupEventListeners();
        setupStorageListener();
        
        // Periodic refresh to sync with content script
        setInterval(loadBlocks, 3000);
        
        // Initialize history
        saveToHistory();
    }
    
    // Setup all event listeners
    function setupEventListeners() {
        // Sidebar tools
        addTextBtn.addEventListener('click', addTextBlock);
        addImageBtn.addEventListener('click', addImageBlock);
        addShapeBtn.addEventListener('click', addShapeBlock);
        selectModeBtn.addEventListener('click', toggleSelectMode);
        exportBtn.addEventListener('click', openExportModal);
        saveTemplateBtn.addEventListener('click', saveAsTemplate);
        resetBtn.addEventListener('click', resetCanvas);
        getDemoBlocksBtn.addEventListener('click', addDemoBlocks);
        openTutorialBtn.addEventListener('click', openTutorial);
        
        // Canvas controls
        undoBtn.addEventListener('click', undo);
        redoBtn.addEventListener('click', redo);
        zoomInBtn.addEventListener('click', zoomIn);
        zoomOutBtn.addEventListener('click', zoomOut);
        fitToScreenBtn.addEventListener('click', fitToScreen);
        
        // Global mouse events
        document.addEventListener('mousemove', handleMouseMove);
        document.addEventListener('mouseup', handleMouseUp);
        document.addEventListener('keydown', handleKeyDown);
        
        // Workspace events
        workspace.addEventListener('click', handleWorkspaceClick);
        
        // Prevent default drag behavior
        document.addEventListener('dragstart', e => e.preventDefault());
    }
    
    // Setup storage listener with error handling
    function setupStorageListener() {
        try {
            if (chrome && chrome.storage && chrome.runtime && chrome.runtime.id) {
                chrome.storage.onChanged.addListener(handleStorageChange);
            }
        } catch (error) {
            console.log('Could not set up storage listener (extension context may be invalidated)');
        }
    }
    
    // Load blocks from storage with fallback
    async function loadBlocks() {
        try {
            // Check if extension context is still valid
            if (!chrome || !chrome.storage || !chrome.runtime || !chrome.runtime.id) {
                loadBlocksFromFallback();
                return;
            }
            
            const result = await chrome.storage.local.get('webLegoBlocks');
            const storedBlocks = result.webLegoBlocks || [];
            
            // Only update if blocks have changed
            if (JSON.stringify(storedBlocks) !== JSON.stringify(blocks)) {
                blocks = storedBlocks;
                renderBlocks();
                updateStats();
            }
        } catch (error) {
            if (error.message.includes('Extension context invalidated')) {
                loadBlocksFromFallback();
            } else {
                console.error('Error loading blocks:', error);
                loadBlocksFromFallback();
            }
        }
    }
    
    // Fallback storage functions
    function loadBlocksFromFallback() {
        try {
            const stored = localStorage.getItem('webLegoBlocks');
            if (stored) {
                const storedBlocks = JSON.parse(stored);
                if (JSON.stringify(storedBlocks) !== JSON.stringify(blocks)) {
                    blocks = storedBlocks;
                    renderBlocks();
                    updateStats();
                }
            }
        } catch (error) {
            console.error('Error loading from fallback storage:', error);
            blocks = [];
            renderBlocks();
            updateStats();
        }
    }
    
    function saveBlocksToFallback() {
        try {
            localStorage.setItem('webLegoBlocks', JSON.stringify(blocks));
        } catch (error) {
            console.error('Error saving to fallback storage:', error);
        }
    }
    
    // Save blocks to storage
    async function saveBlocks() {
        try {
            // Check if extension context is still valid
            if (!chrome || !chrome.storage || !chrome.runtime || !chrome.runtime.id) {
                saveBlocksToFallback();
                return;
            }
            
            await chrome.storage.local.set({ webLegoBlocks: blocks });
            saveBlocksToFallback(); // Always save to fallback as backup
        } catch (error) {
            if (error.message.includes('Extension context invalidated')) {
                saveBlocksToFallback();
            } else {
                console.error('Error saving blocks:', error);
                saveBlocksToFallback();
            }
        }
    }
    
    // Handle storage changes
    function handleStorageChange(changes, namespace) {
        try {
            if (namespace === 'local' && changes.webLegoBlocks) {
                blocks = changes.webLegoBlocks.newValue || [];
                renderBlocks();
                updateStats();
            }
        } catch (error) {
            console.log('Storage change handler error:', error);
        }
    }
    
    // Add different types of blocks
    function addTextBlock() {
        const block = {
            id: 'text-' + Date.now() + '-' + nextBlockId++,
            type: 'text',
            content: '<div style="padding: 20px; font-family: -apple-system, BlinkMacSystemFont, \'Segoe UI\', sans-serif;"><h3 style="margin: 0 0 10px; color: #2d3748;">New Text Block</h3><p style="margin: 0; color: #4a5568;">Double-click to edit this text. You can format it however you like!</p></div>',
            width: 300,
            height: 120,
            x: 50 + (blocks.length * 20),
            y: 50 + (blocks.length * 20),
            timestamp: Date.now(),
            editable: true
        };
        
        blocks.push(block);
        saveBlocks();
        renderBlocks();
        updateStats();
        saveToHistory();
        showNotification('Text block added!');
    }
    
    function addImageBlock() {
        const block = {
            id: 'image-' + Date.now() + '-' + nextBlockId++,
            type: 'image',
            content: '<div style="padding: 15px; text-align: center; background: linear-gradient(45deg, #667eea, #764ba2); border-radius: 12px;"><div style="width: 200px; height: 150px; background: rgba(255,255,255,0.2); border-radius: 8px; display: flex; align-items: center; justify-content: center; color: white; font-size: 24px; margin: 0 auto;">🖼️</div><p style="margin: 10px 0 0; color: white; font-weight: 500;">Image Placeholder</p></div>',
            width: 250,
            height: 200,
            x: 80 + (blocks.length * 20),
            y: 80 + (blocks.length * 20),
            timestamp: Date.now(),
            editable: true
        };
        
        blocks.push(block);
        saveBlocks();
        renderBlocks();
        updateStats();
        saveToHistory();
        showNotification('Image block added!');
    }
    
    function addShapeBlock() {
        const colors = ['#ff6b6b', '#4ecdc4', '#45b7d1', '#96ceb4', '#feca57', '#ff9ff3'];
        const randomColor = colors[Math.floor(Math.random() * colors.length)];
        
        const block = {
            id: 'shape-' + Date.now() + '-' + nextBlockId++,
            type: 'shape',
            content: `<div style="width: 100%; height: 100%; background: ${randomColor}; border-radius: 12px; display: flex; align-items: center; justify-content: center; color: white; font-size: 20px; font-weight: bold;">✨</div>`,
            width: 150,
            height: 150,
            x: 120 + (blocks.length * 20),
            y: 120 + (blocks.length * 20),
            timestamp: Date.now(),
            editable: true
        };
        
        blocks.push(block);
        saveBlocks();
        renderBlocks();
        updateStats();
        saveToHistory();
        showNotification('Shape block added!');
    }
    
    // Render all blocks
    function renderBlocks() {
        // Clear existing blocks
        const existingBlocks = workspace.querySelectorAll('.block');
        existingBlocks.forEach(block => block.remove());
        
        // Show/hide empty state
        if (blocks.length === 0) {
            emptyState.style.display = 'block';
        } else {
            emptyState.style.display = 'none';
        }
        
        // Render each block
        blocks.forEach(block => {
            createBlockElement(block);
        });
    }
    
    // Create a block element with enhanced features
    function createBlockElement(blockData) {
        const blockEl = document.createElement('div');
        blockEl.className = 'block block-appear';
        blockEl.dataset.blockId = blockData.id;
        
        // Set position and size
        blockEl.style.left = blockData.x + 'px';
        blockEl.style.top = blockData.y + 'px';
        blockEl.style.width = blockData.width + 'px';
        blockEl.style.height = blockData.height + 'px';
        blockEl.style.zIndex = blockData.zIndex || 1;
        
        // Create enhanced block structure
        blockEl.innerHTML = `
            <div class="block-toolbar">
                <div class="block-drag-handle">
                    <span>⋮⋮</span>
                    <span style="font-size: 10px;">${blockData.type || 'block'}</span>
                </div>
                <div class="block-actions">
                    <button class="block-action edit" title="Edit content">✏️</button>
                    <button class="block-action duplicate" title="Duplicate">📋</button>
                    <button class="block-action delete" title="Delete">×</button>
                </div>
            </div>
            <div class="block-content" ${blockData.editable ? 'data-editable="true"' : ''}>${blockData.content}</div>
            <div class="block-resize"></div>
        `;
        
        // Add enhanced event listeners
        setupBlockEvents(blockEl, blockData);
        
        workspace.appendChild(blockEl);
    }
    
    // Setup enhanced block events
    function setupBlockEvents(blockEl, blockData) {
        const toolbar = blockEl.querySelector('.block-toolbar');
        const content = blockEl.querySelector('.block-content');
        const editBtn = blockEl.querySelector('.block-action.edit');
        const duplicateBtn = blockEl.querySelector('.block-action.duplicate');
        const deleteBtn = blockEl.querySelector('.block-action.delete');
        const resizeHandle = blockEl.querySelector('.block-resize');
        
        // Selection
        blockEl.addEventListener('click', (e) => {
            if (e.target.closest('.block-toolbar')) return;
            selectBlock(blockEl, blockData);
        });
        
        // Drag events
        toolbar.addEventListener('mousedown', e => startDrag(e, blockEl, blockData));
        
        // Edit events
        editBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            startEditing(blockEl, blockData);
        });
        
        // Double-click to edit
        content.addEventListener('dblclick', () => {
            if (blockData.editable) {
                startEditing(blockEl, blockData);
            }
        });
        
        // Duplicate event
        duplicateBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            duplicateBlock(blockData);
        });
        
        // Delete event
        deleteBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            deleteBlock(blockData.id);
        });
        
        // Resize events
        resizeHandle.addEventListener('mousedown', e => startResize(e, blockEl, blockData));
    }
    
    // Block selection
    function selectBlock(blockEl, blockData) {
        // Clear previous selection
        document.querySelectorAll('.block.selected').forEach(el => {
            el.classList.remove('selected');
        });
        
        // Select current block
        blockEl.classList.add('selected');
        selectedBlock = { element: blockEl, data: blockData };
    }
    
    // Start editing block content
    function startEditing(blockEl, blockData) {
        const content = blockEl.querySelector('.block-content');
        
        if (!blockData.editable) {
            showNotification('This block is not editable');
            return;
        }
        
        content.contentEditable = true;
        content.focus();
        
        // Select all text for easy editing
        const range = document.createRange();
        range.selectNodeContents(content);
        const selection = window.getSelection();
        selection.removeAllRanges();
        selection.addRange(range);
        
        // Handle finish editing
        const finishEditing = () => {
            content.contentEditable = false;
            blockData.content = content.innerHTML;
            saveBlocks();
            saveToHistory();
            showNotification('Block updated!');
        };
        
        // Finish editing on blur or Enter key
        content.addEventListener('blur', finishEditing, { once: true });
        content.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                finishEditing();
            }
        }, { once: true });
    }
    
    // Duplicate block
    function duplicateBlock(blockData) {
        const newBlock = {
            ...blockData,
            id: blockData.type + '-' + Date.now() + '-' + nextBlockId++,
            x: blockData.x + 20,
            y: blockData.y + 20,
            timestamp: Date.now()
        };
        
        blocks.push(newBlock);
        saveBlocks();
        renderBlocks();
        updateStats();
        saveToHistory();
        showNotification('Block duplicated!');
    }
    
    // Enhanced drag functionality
    function startDrag(e, blockEl, blockData) {
        if (e.target.closest('.block-action')) return;
        
        e.preventDefault();
        
        draggedBlock = { element: blockEl, data: blockData };
        
        const rect = blockEl.getBoundingClientRect();
        const workspaceRect = workspace.getBoundingClientRect();
        
        dragOffset.x = e.clientX - rect.left;
        dragOffset.y = e.clientY - rect.top;
        
        blockEl.classList.add('dragging');
        document.body.style.userSelect = 'none';
        
        // Bring to front
        blockEl.style.zIndex = 1000;
    }
    
    function handleMouseMove(e) {
        if (draggedBlock) {
            handleDrag(e);
        } else if (resizingBlock) {
            handleResize(e);
        }
    }
    
    function handleDrag(e) {
        if (!draggedBlock) return;
        
        const workspaceRect = workspace.getBoundingClientRect();
        
        let newX = e.clientX - workspaceRect.left - dragOffset.x + workspace.scrollLeft;
        let newY = e.clientY - workspaceRect.top - dragOffset.y + workspace.scrollTop;
        
        // Allow negative positions for overlapping
        newX = Math.max(-100, newX);
        newY = Math.max(-100, newY);
        
        // Update position
        draggedBlock.element.style.left = newX + 'px';
        draggedBlock.element.style.top = newY + 'px';
        
        // Update data
        draggedBlock.data.x = newX;
        draggedBlock.data.y = newY;
    }
    
    function handleMouseUp(e) {
        if (draggedBlock) {
            draggedBlock.element.classList.remove('dragging');
            draggedBlock.element.style.zIndex = draggedBlock.data.zIndex || 1;
            draggedBlock = null;
            document.body.style.userSelect = '';
            
            saveBlocks();
            saveToHistory();
        }
        
        if (resizingBlock) {
            resizingBlock = null;
            document.body.style.cursor = '';
            document.body.style.userSelect = '';
            
            saveBlocks();
            saveToHistory();
        }
    }
    
    // Enhanced resize functionality
    function startResize(e, blockEl, blockData) {
        e.preventDefault();
        e.stopPropagation();
        
        resizingBlock = { element: blockEl, data: blockData };
        
        resizeStartPos.x = e.clientX;
        resizeStartPos.y = e.clientY;
        
        const rect = blockEl.getBoundingClientRect();
        resizeStartSize.width = rect.width;
        resizeStartSize.height = rect.height;
        
        document.body.style.cursor = 'nw-resize';
        document.body.style.userSelect = 'none';
    }
    
    function handleResize(e) {
        if (!resizingBlock) return;
        
        const deltaX = e.clientX - resizeStartPos.x;
        const deltaY = e.clientY - resizeStartPos.y;
        
        let newWidth = Math.max(100, resizeStartSize.width + deltaX);
        let newHeight = Math.max(50, resizeStartSize.height + deltaY);
        
        // Update size
        resizingBlock.element.style.width = newWidth + 'px';
        resizingBlock.element.style.height = newHeight + 'px';
        
        // Update data
        resizingBlock.data.width = newWidth;
        resizingBlock.data.height = newHeight;
    }
    
    // Delete block with animation
    function deleteBlock(blockId) {
        const blockEl = document.querySelector(`[data-block-id="${blockId}"]`);
        
        if (blockEl) {
            blockEl.classList.add('block-remove');
            
            setTimeout(() => {
                blocks = blocks.filter(block => block.id !== blockId);
                saveBlocks();
                renderBlocks();
                updateStats();
                saveToHistory();
                showNotification('Block deleted!');
            }, 300);
        }
    }
    
    // History management
    function saveToHistory() {
        // Remove any future history if we're not at the end
        history = history.slice(0, historyIndex + 1);
        
        // Add current state
        history.push(JSON.stringify(blocks));
        historyIndex++;
        
        // Limit history size
        if (history.length > 50) {
            history.shift();
            historyIndex--;
        }
        
        updateHistoryButtons();
    }
    
    function undo() {
        if (historyIndex > 0) {
            historyIndex--;
            blocks = JSON.parse(history[historyIndex]);
            saveBlocks();
            renderBlocks();
            updateStats();
            updateHistoryButtons();
            showNotification('Undone!');
        }
    }
    
    function redo() {
        if (historyIndex < history.length - 1) {
            historyIndex++;
            blocks = JSON.parse(history[historyIndex]);
            saveBlocks();
            renderBlocks();
            updateStats();
            updateHistoryButtons();
            showNotification('Redone!');
        }
    }
    
    function updateHistoryButtons() {
        undoBtn.disabled = historyIndex <= 0;
        redoBtn.disabled = historyIndex >= history.length - 1;
    }
    
    // Zoom and view controls
    function zoomIn() {
        zoom = Math.min(zoom * 1.2, 3);
        applyZoom();
    }
    
    function zoomOut() {
        zoom = Math.max(zoom / 1.2, 0.3);
        applyZoom();
    }
    
    function fitToScreen() {
        zoom = 1;
        applyZoom();
        workspace.scrollTo(0, 0);
        showNotification('Fit to screen');
    }
    
    function applyZoom() {
        workspace.style.transform = `scale(${zoom})`;
        workspace.style.transformOrigin = '0 0';
    }
    
    // Update statistics
    function updateStats() {
        const count = blocks.length;
        blockCount.textContent = count;
        
        // Calculate layers (overlapping blocks)
        const layers = Math.max(1, Math.ceil(count / 5));
        layerCount.textContent = layers;
        
        // Show offline indicator if needed
        if (!chrome || !chrome.storage || !chrome.runtime || !chrome.runtime.id) {
            blockCount.textContent += ' (offline)';
        }
    }
    
    // Export functionality
    function openExportModal() {
        const modal = document.getElementById('exportModal');
        modal.classList.add('active');
    }
    
    function closeExportModal() {
        const modal = document.getElementById('exportModal');
        modal.classList.remove('active');
    }
    
    // Make closeExportModal globally available
    window.closeExportModal = closeExportModal;
    
    function exportAsHTML() {
        const html = generateHTML();
        downloadFile('web-lego-layout.html', html, 'text/html');
        closeExportModal();
        showNotification('HTML file downloaded!');
    }
    
    function exportAsImage() {
        // This would require html2canvas or similar library
        showNotification('Image export coming soon!');
        closeExportModal();
    }
    
    function exportAsCode() {
        const html = generateHTML();
        
        // Create a modal to show the code
        const codeModal = document.createElement('div');
        codeModal.innerHTML = `
            <div style="position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.7); display: flex; align-items: center; justify-content: center; z-index: 3000;">
                <div style="background: white; border-radius: 12px; padding: 30px; max-width: 80%; max-height: 80%; overflow-y: auto;">
                    <h3>Your HTML Code</h3>
                    <textarea style="width: 100%; height: 400px; font-family: monospace; font-size: 12px; margin: 15px 0;" readonly>${html}</textarea>
                    <div style="display: flex; gap: 10px;">
                        <button onclick="navigator.clipboard.writeText(this.parentElement.previousElementSibling.value); this.textContent='Copied!'" style="padding: 8px 16px; background: #667eea; color: white; border: none; border-radius: 6px;">Copy Code</button>
                        <button onclick="this.closest('div').remove()" style="padding: 8px 16px; background: #e2e8f0; color: #4a5568; border: none; border-radius: 6px;">Close</button>
                    </div>
                </div>
            </div>
        `;
        
        document.body.appendChild(codeModal);
        closeExportModal();
    }
    
    function shareLayout() {
        // Generate a shareable link (this would typically involve a backend service)
        const layoutData = btoa(JSON.stringify(blocks));
        const shareUrl = `${window.location.origin}${window.location.pathname}?layout=${layoutData}`;
        
        navigator.clipboard.writeText(shareUrl).then(() => {
            showNotification('Share link copied to clipboard!');
        }).catch(() => {
            showNotification('Could not copy share link');
        });
        
        closeExportModal();
    }
    
    // Make export functions globally available
    window.exportAsHTML = exportAsHTML;
    window.exportAsImage = exportAsImage;
    window.exportAsCode = exportAsCode;
    window.shareLayout = shareLayout;
    
    function generateHTML() {
        let html = `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Web Lego Layout</title>
    <style>
        body { margin: 0; padding: 20px; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #f8fafc; }
        .layout-container { position: relative; min-height: 100vh; }
        .layout-block { position: absolute; background: white; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); overflow: hidden; }
    </style>
</head>
<body>
    <div class="layout-container">
`;
        
        blocks.forEach(block => {
            html += `        <div class="layout-block" style="left: ${block.x}px; top: ${block.y}px; width: ${block.width}px; height: ${block.height}px; z-index: ${block.zIndex || 1};">
            ${block.content}
        </div>
`;
        });
        
        html += `    </div>
</body>
</html>`;
        
        return html;
    }
    
    function downloadFile(filename, content, contentType) {
        const blob = new Blob([content], { type: contentType });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        a.click();
        URL.revokeObjectURL(url);
    }
    
    // Other utility functions
    function saveAsTemplate() {
        const templateName = prompt('Enter template name:');
        if (templateName) {
            const templates = JSON.parse(localStorage.getItem('webLegoTemplates') || '{}');
            templates[templateName] = blocks;
            localStorage.setItem('webLegoTemplates', JSON.stringify(templates));
            showNotification(`Template "${templateName}" saved!`);
        }
    }
    
    function toggleSelectMode() {
        // This would integrate with the content script
        showNotification('Switch to webpage to select elements');
    }
    
    function resetCanvas() {
        if (confirm('Are you sure you want to clear the canvas? This cannot be undone.')) {
            blocks = [];
            saveBlocks();
            renderBlocks();
            updateStats();
            saveToHistory();
            showNotification('Canvas cleared!');
        }
    }
    
    function addDemoBlocks() {
        const demoBlocks = [
            {
                id: 'demo-welcome-' + Date.now(),
                type: 'text',
                content: '<div style="padding: 30px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border-radius: 16px; text-align: center;"><h2 style="margin: 0 0 15px; font-size: 28px;">🧱 Welcome to Web Lego!</h2><p style="margin: 0; font-size: 16px; opacity: 0.9;">Build amazing layouts by dragging, editing, and arranging blocks!</p></div>',
                width: 400,
                height: 150,
                x: 50,
                y: 50,
                timestamp: Date.now(),
                editable: true
            },
            {
                id: 'demo-features-' + Date.now(),
                type: 'text',
                content: '<div style="padding: 25px; background: white; border-radius: 12px; border-left: 4px solid #4ecdc4;"><h3 style="margin: 0 0 15px; color: #2d3748;">✨ Amazing Features</h3><ul style="margin: 0; padding-left: 20px; color: #4a5568; line-height: 1.6;"><li>Drag & drop blocks anywhere</li><li>Double-click to edit text</li><li>Resize blocks by dragging corners</li><li>Export as HTML or share links</li><li>Overlap blocks for complex layouts</li></ul></div>',
                width: 320,
                height: 180,
                x: 500,
                y: 80,
                timestamp: Date.now() + 1,
                editable: true
            },
            {
                id: 'demo-image-' + Date.now(),
                type: 'image',
                content: '<div style="padding: 20px; background: linear-gradient(45deg, #ff6b6b, #4ecdc4); border-radius: 12px; text-align: center; color: white;"><div style="width: 180px; height: 120px; background: rgba(255,255,255,0.2); border-radius: 8px; display: flex; align-items: center; justify-content: center; font-size: 40px; margin: 0 auto 15px;">🎨</div><h4 style="margin: 0; font-size: 16px;">Creative Canvas</h4></div>',
                width: 220,
                height: 200,
                x: 150,
                y: 250,
                timestamp: Date.now() + 2,
                editable: true
            }
        ];
        
        blocks = [...blocks, ...demoBlocks];
        saveBlocks();
        renderBlocks();
        updateStats();
        saveToHistory();
        showNotification('Demo blocks added!');
    }
    
    function openTutorial() {
        showNotification('Tutorial coming soon! For now, try the demo blocks.');
    }
    
    function handleWorkspaceClick(e) {
        if (e.target === workspace) {
            // Deselect all blocks when clicking empty space
            document.querySelectorAll('.block.selected').forEach(el => {
                el.classList.remove('selected');
            });
            selectedBlock = null;
        }
    }
    
    function handleKeyDown(e) {
        if (e.key === 'Delete' && selectedBlock) {
            deleteBlock(selectedBlock.data.id);
        }
        
        if (e.ctrlKey || e.metaKey) {
            if (e.key === 'z' && !e.shiftKey) {
                e.preventDefault();
                undo();
            } else if (e.key === 'z' && e.shiftKey || e.key === 'y') {
                e.preventDefault();
                redo();
            }
        }
    }
    
    // Show notification
    function showNotification(message) {
        const notification = document.createElement('div');
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: #48bb78;
            color: white;
            padding: 12px 20px;
            border-radius: 8px;
            font-size: 14px;
            font-weight: 500;
            box-shadow: 0 4px 12px rgba(72, 187, 120, 0.3);
            z-index: 10000;
            animation: slideIn 0.3s ease-out;
        `;
        
        notification.textContent = message;
        document.body.appendChild(notification);
        
        // Auto-remove after 3 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.style.animation = 'slideIn 0.3s ease-out reverse';
                setTimeout(() => {
                    if (notification.parentNode) {
                        notification.parentNode.removeChild(notification);
                    }
                }, 300);
            }
        }, 3000);
    }
    
    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initCanvas);
    } else {
        initCanvas();
    }
    
})();
