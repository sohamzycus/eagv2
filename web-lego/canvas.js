// Canvas script for Web Lego extension
// Handles draggable blocks, resizing, and canvas management

(function() {
    'use strict';
    
    // Global state
    let blocks = [];
    let draggedBlock = null;
    let dragOffset = { x: 0, y: 0 };
    let resizingBlock = null;
    let resizeStartPos = { x: 0, y: 0 };
    let resizeStartSize = { width: 0, height: 0 };
    
    // DOM elements
    const workspace = document.getElementById('workspace');
    const emptyState = document.getElementById('emptyState');
    const blockCount = document.getElementById('blockCount');
    const resetBtn = document.getElementById('resetBtn');
    const saveBtn = document.getElementById('saveBtn');
    const getDemoBlocksBtn = document.getElementById('getDemoBlocks');
    
    // Initialize canvas
    function initCanvas() {
        loadBlocks();
        setupEventListeners();
        
        // Listen for storage changes from content script
        if (chrome && chrome.storage) {
            chrome.storage.onChanged.addListener(handleStorageChange);
        }
        
        // Periodic refresh to sync with content script
        setInterval(loadBlocks, 2000);
    }
    
    // Setup event listeners
    function setupEventListeners() {
        resetBtn.addEventListener('click', resetCanvas);
        saveBtn.addEventListener('click', saveCanvas);
        getDemoBlocksBtn.addEventListener('click', addDemoBlocks);
        
        // Global mouse events for drag and resize
        document.addEventListener('mousemove', handleMouseMove);
        document.addEventListener('mouseup', handleMouseUp);
        
        // Prevent default drag behavior
        document.addEventListener('dragstart', e => e.preventDefault());
    }
    
    // Load blocks from storage
    async function loadBlocks() {
        try {
            if (chrome && chrome.storage) {
                const result = await chrome.storage.local.get('webLegoBlocks');
                const storedBlocks = result.webLegoBlocks || [];
                
                // Only update if blocks have changed
                if (JSON.stringify(storedBlocks) !== JSON.stringify(blocks)) {
                    blocks = storedBlocks;
                    renderBlocks();
                }
            }
        } catch (error) {
            console.error('Error loading blocks:', error);
        }
    }
    
    // Handle storage changes
    function handleStorageChange(changes, namespace) {
        if (namespace === 'local' && changes.webLegoBlocks) {
            blocks = changes.webLegoBlocks.newValue || [];
            renderBlocks();
        }
    }
    
    // Render all blocks
    function renderBlocks() {
        // Clear existing blocks
        const existingBlocks = workspace.querySelectorAll('.block');
        existingBlocks.forEach(block => block.remove());
        
        // Show/hide empty state
        if (blocks.length === 0) {
            emptyState.style.display = 'block';
            blockCount.textContent = '0 blocks';
        } else {
            emptyState.style.display = 'none';
            blockCount.textContent = `${blocks.length} block${blocks.length !== 1 ? 's' : ''}`;
        }
        
        // Render each block
        blocks.forEach(block => {
            createBlockElement(block);
        });
    }
    
    // Create a block element
    function createBlockElement(blockData) {
        const blockEl = document.createElement('div');
        blockEl.className = 'block block-appear';
        blockEl.dataset.blockId = blockData.id;
        
        // Set position and size
        blockEl.style.left = blockData.x + 'px';
        blockEl.style.top = blockData.y + 'px';
        blockEl.style.width = blockData.width + 'px';
        blockEl.style.height = blockData.height + 'px';
        
        // Create block structure
        blockEl.innerHTML = `
            <div class="block-header">
                <div class="block-drag-handle">⋮⋮</div>
                <button class="block-delete" title="Delete block">×</button>
            </div>
            <div class="block-content">${blockData.content}</div>
            <div class="block-resize"></div>
        `;
        
        // Add event listeners
        setupBlockEvents(blockEl, blockData);
        
        workspace.appendChild(blockEl);
    }
    
    // Setup events for a block
    function setupBlockEvents(blockEl, blockData) {
        const header = blockEl.querySelector('.block-header');
        const deleteBtn = blockEl.querySelector('.block-delete');
        const resizeHandle = blockEl.querySelector('.block-resize');
        
        // Drag events
        header.addEventListener('mousedown', e => startDrag(e, blockEl, blockData));
        blockEl.addEventListener('mousedown', e => {
            if (e.target === blockEl || e.target.closest('.block-content')) {
                startDrag(e, blockEl, blockData);
            }
        });
        
        // Delete event
        deleteBtn.addEventListener('click', e => {
            e.stopPropagation();
            deleteBlock(blockData.id);
        });
        
        // Resize events
        resizeHandle.addEventListener('mousedown', e => startResize(e, blockEl, blockData));
    }
    
    // Start dragging a block
    function startDrag(e, blockEl, blockData) {
        if (e.target.closest('.block-delete') || e.target.closest('.block-resize')) {
            return;
        }
        
        e.preventDefault();
        
        draggedBlock = { element: blockEl, data: blockData };
        
        const rect = blockEl.getBoundingClientRect();
        const workspaceRect = workspace.getBoundingClientRect();
        
        dragOffset.x = e.clientX - rect.left;
        dragOffset.y = e.clientY - rect.top;
        
        blockEl.classList.add('dragging');
        document.body.style.userSelect = 'none';
    }
    
    // Start resizing a block
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
    
    // Handle mouse move for drag and resize
    function handleMouseMove(e) {
        if (draggedBlock) {
            handleDrag(e);
        } else if (resizingBlock) {
            handleResize(e);
        }
    }
    
    // Handle dragging
    function handleDrag(e) {
        if (!draggedBlock) return;
        
        const workspaceRect = workspace.getBoundingClientRect();
        
        let newX = e.clientX - workspaceRect.left - dragOffset.x + workspace.scrollLeft;
        let newY = e.clientY - workspaceRect.top - dragOffset.y + workspace.scrollTop;
        
        // Keep block within workspace bounds
        newX = Math.max(0, Math.min(newX, workspace.scrollWidth - draggedBlock.element.offsetWidth));
        newY = Math.max(0, Math.min(newY, workspace.scrollHeight - draggedBlock.element.offsetHeight));
        
        // Update position
        draggedBlock.element.style.left = newX + 'px';
        draggedBlock.element.style.top = newY + 'px';
        
        // Update data
        draggedBlock.data.x = newX;
        draggedBlock.data.y = newY;
    }
    
    // Handle resizing
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
    
    // Handle mouse up
    function handleMouseUp(e) {
        if (draggedBlock) {
            draggedBlock.element.classList.remove('dragging');
            draggedBlock = null;
            document.body.style.userSelect = '';
            
            // Save updated positions
            saveBlocks();
        }
        
        if (resizingBlock) {
            resizingBlock = null;
            document.body.style.cursor = '';
            document.body.style.userSelect = '';
            
            // Save updated sizes
            saveBlocks();
        }
    }
    
    // Delete a block
    function deleteBlock(blockId) {
        const blockEl = document.querySelector(`[data-block-id="${blockId}"]`);
        
        if (blockEl) {
            blockEl.classList.add('block-remove');
            
            setTimeout(() => {
                // Remove from blocks array
                blocks = blocks.filter(block => block.id !== blockId);
                
                // Update storage
                saveBlocks();
                
                // Re-render
                renderBlocks();
            }, 200);
        }
    }
    
    // Save blocks to storage
    async function saveBlocks() {
        try {
            if (chrome && chrome.storage) {
                await chrome.storage.local.set({ webLegoBlocks: blocks });
            }
        } catch (error) {
            console.error('Error saving blocks:', error);
        }
    }
    
    // Reset canvas
    async function resetCanvas() {
        if (confirm('Are you sure you want to remove all blocks? This cannot be undone.')) {
            blocks = [];
            
            try {
                if (chrome && chrome.storage) {
                    await chrome.storage.local.set({ webLegoBlocks: [] });
                }
            } catch (error) {
                console.error('Error clearing storage:', error);
            }
            
            renderBlocks();
            
            // Show success feedback
            showNotification('Canvas cleared!');
        }
    }
    
    // Save canvas (show feedback)
    function saveCanvas() {
        saveBlocks();
        showNotification('Layout saved!');
    }
    
    // Add demo blocks
    async function addDemoBlocks() {
        const demoBlocks = [
            {
                id: 'demo-welcome-' + Date.now(),
                content: '<div style="padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border-radius: 12px; font-family: -apple-system, BlinkMacSystemFont, \'Segoe UI\', sans-serif;"><h3 style="margin: 0 0 10px;">🧱 Welcome to Web Lego!</h3><p style="margin: 0; opacity: 0.9;">Drag me around, resize me, or delete me. Start building something amazing!</p></div>',
                type: 'div',
                width: 320,
                height: 120,
                x: 50,
                y: 50,
                timestamp: Date.now()
            },
            {
                id: 'demo-quote-' + Date.now(),
                content: '<blockquote style="margin: 0; padding: 20px; background: #f7fafc; border-left: 4px solid #4299e1; border-radius: 8px; font-style: italic; color: #2d3748; font-family: -apple-system, BlinkMacSystemFont, \'Segoe UI\', sans-serif;"><p style="margin: 0 0 10px;">"Creativity is intelligence having fun."</p><footer style="margin: 0; font-size: 14px; color: #718096; font-style: normal;">— Albert Einstein</footer></blockquote>',
                type: 'blockquote',
                width: 350,
                height: 110,
                x: 400,
                y: 80,
                timestamp: Date.now() + 1
            },
            {
                id: 'demo-card-' + Date.now(),
                content: '<div style="padding: 20px; background: white; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); font-family: -apple-system, BlinkMacSystemFont, \'Segoe UI\', sans-serif;"><div style="width: 100%; height: 80px; background: linear-gradient(45deg, #ff6b6b, #4ecdc4, #45b7d1); border-radius: 8px; display: flex; align-items: center; justify-content: center; color: white; font-size: 18px; font-weight: bold; margin-bottom: 15px;">🎨 Demo Card</div><h4 style="margin: 0 0 8px; color: #2d3748;">Interactive Block</h4><p style="margin: 0; color: #718096; font-size: 14px; line-height: 1.4;">This is a sample content block. You can drag, resize, and customize any element from any webpage!</p></div>',
                type: 'div',
                width: 280,
                height: 200,
                x: 120,
                y: 220,
                timestamp: Date.now() + 2
            }
        ];
        
        // Add demo blocks to existing blocks
        blocks = [...blocks, ...demoBlocks];
        
        // Save to storage
        await saveBlocks();
        
        // Re-render
        renderBlocks();
        
        // Show notification
        showNotification('Demo blocks added!');
    }
    
    // Show notification
    function showNotification(message) {
        // Create notification element
        const notification = document.createElement('div');
        notification.style.cssText = `
            position: fixed;
            top: 80px;
            right: 20px;
            background: #48bb78;
            color: white;
            padding: 12px 20px;
            border-radius: 8px;
            font-size: 14px;
            font-weight: 500;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            z-index: 10000;
            animation: slideIn 0.3s ease-out;
        `;
        
        notification.textContent = message;
        document.body.appendChild(notification);
        
        // Add animation styles
        const style = document.createElement('style');
        style.textContent = `
            @keyframes slideIn {
                from {
                    transform: translateX(100%);
                    opacity: 0;
                }
                to {
                    transform: translateX(0);
                    opacity: 1;
                }
            }
        `;
        document.head.appendChild(style);
        
        // Auto-remove after 3 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.style.animation = 'slideIn 0.3s ease-out reverse';
                setTimeout(() => {
                    if (notification.parentNode) {
                        notification.parentNode.removeChild(notification);
                    }
                    if (style.parentNode) {
                        style.parentNode.removeChild(style);
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
