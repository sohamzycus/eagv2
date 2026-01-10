"""
fDOM MAP Visualization - State Graph Visualization for fDOM
Creates interactive visual representation of UI state navigation
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime
import math


@dataclass
class StateNode:
    """Represents a state node in the visualization"""
    id: str
    label: str
    x: float
    y: float
    element_count: int
    is_root: bool = False
    parent: Optional[str] = None
    

@dataclass  
class StateEdge:
    """Represents an edge between states"""
    from_state: str
    to_state: str
    trigger_element: str
    action: str


class FDOMMapGenerator:
    """
    Generates interactive HTML visualization of fDOM state graph
    """
    
    def __init__(self, fdom_path: str = None):
        self.fdom_data: Dict = {}
        self.nodes: List[StateNode] = []
        self.edges: List[StateEdge] = []
        
        if fdom_path:
            self.load_fdom(fdom_path)
    
    def load_fdom(self, fdom_path: str) -> bool:
        """Load fDOM data from JSON file"""
        try:
            with open(fdom_path, 'r', encoding='utf-8') as f:
                self.fdom_data = json.load(f)
            self._parse_fdom()
            return True
        except Exception as e:
            print(f"Error loading fDOM: {e}")
            return False
    
    def load_fdom_dict(self, fdom_data: Dict) -> bool:
        """Load fDOM data from dictionary"""
        self.fdom_data = fdom_data
        self._parse_fdom()
        return True
    
    def _parse_fdom(self):
        """Parse fDOM data into nodes and edges"""
        states = self.fdom_data.get("states", {})
        edges_data = self.fdom_data.get("edges", [])
        
        # Calculate node positions using force-directed layout simulation
        positions = self._calculate_positions(states, edges_data)
        
        # Create nodes
        self.nodes = []
        for state_id, state_data in states.items():
            pos = positions.get(state_id, (400, 300))
            node = StateNode(
                id=state_id,
                label=state_data.get("breadcrumb", state_id).split(">")[-1],
                x=pos[0],
                y=pos[1],
                element_count=state_data.get("total_elements", len(state_data.get("nodes", {}))),
                is_root=(state_id == "root"),
                parent=state_data.get("parent")
            )
            self.nodes.append(node)
        
        # Create edges
        self.edges = []
        for edge_data in edges_data:
            edge = StateEdge(
                from_state=edge_data.get("from", ""),
                to_state=edge_data.get("to", ""),
                trigger_element=edge_data.get("element_name", ""),
                action=edge_data.get("action", "")
            )
            self.edges.append(edge)
    
    def _calculate_positions(self, states: Dict, edges: List) -> Dict[str, Tuple[float, float]]:
        """Calculate node positions using radial tree layout"""
        positions = {}
        
        if not states:
            return positions
        
        # Start with root at center
        center_x, center_y = 500, 400
        positions["root"] = (center_x, center_y)
        
        # Build adjacency list
        children = {}
        for state_id in states:
            parent = states[state_id].get("parent")
            if parent:
                if parent not in children:
                    children[parent] = []
                children[parent].append(state_id)
        
        # Position children in circles around their parents
        def position_children(parent_id: str, level: int = 1):
            if parent_id not in children:
                return
            
            parent_pos = positions.get(parent_id, (center_x, center_y))
            child_list = children[parent_id]
            num_children = len(child_list)
            
            # Calculate radius based on level
            radius = 150 + (level * 80)
            
            # Calculate angle offset to spread children
            if parent_id == "root":
                start_angle = -math.pi / 2  # Start from top
            else:
                # Get angle from parent to grandparent
                grandparent = states[parent_id].get("parent")
                if grandparent and grandparent in positions:
                    gp_pos = positions[grandparent]
                    dx = parent_pos[0] - gp_pos[0]
                    dy = parent_pos[1] - gp_pos[1]
                    start_angle = math.atan2(dy, dx)
                else:
                    start_angle = 0
            
            angle_step = (2 * math.pi) / max(num_children, 4) if num_children > 0 else 0
            
            for i, child_id in enumerate(child_list):
                angle = start_angle + (i - (num_children - 1) / 2) * angle_step * 0.8
                x = parent_pos[0] + radius * math.cos(angle)
                y = parent_pos[1] + radius * math.sin(angle)
                positions[child_id] = (x, y)
            
            # Recursively position grandchildren
            for child_id in child_list:
                position_children(child_id, level + 1)
        
        position_children("root")
        
        # Handle orphan states (no parent)
        orphan_y = 100
        for state_id in states:
            if state_id not in positions:
                positions[state_id] = (100, orphan_y)
                orphan_y += 80
        
        return positions
    
    def generate_html(self, output_path: str = None, title: str = "fDOM State Map") -> str:
        """Generate interactive HTML visualization"""
        
        # Prepare nodes data for JavaScript
        nodes_js = []
        for node in self.nodes:
            nodes_js.append({
                "id": node.id,
                "label": node.label,
                "x": node.x,
                "y": node.y,
                "elements": node.element_count,
                "isRoot": node.is_root,
                "parent": node.parent
            })
        
        # Prepare edges data for JavaScript
        edges_js = []
        for edge in self.edges:
            edges_js.append({
                "from": edge.from_state,
                "to": edge.to_state,
                "trigger": edge.trigger_element,
                "action": edge.action
            })
        
        # Get exploration stats
        stats = self.fdom_data.get("exploration_stats", {})
        app_name = self.fdom_data.get("app_name", "Unknown App")
        
        html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'JetBrains Mono', 'SF Mono', monospace;
            background: linear-gradient(135deg, #0a0a0f 0%, #1a1a2e 50%, #0f0f23 100%);
            min-height: 100vh;
            color: #e0e0e0;
            overflow: hidden;
        }}
        
        .header {{
            background: linear-gradient(90deg, rgba(99, 102, 241, 0.1), rgba(139, 92, 246, 0.1));
            border-bottom: 1px solid rgba(139, 92, 246, 0.3);
            padding: 20px 30px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        
        .header h1 {{
            font-size: 24px;
            font-weight: 600;
            background: linear-gradient(120deg, #818cf8, #c084fc);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            letter-spacing: -0.5px;
        }}
        
        .stats {{
            display: flex;
            gap: 30px;
        }}
        
        .stat {{
            text-align: center;
        }}
        
        .stat-value {{
            font-size: 28px;
            font-weight: 700;
            color: #818cf8;
        }}
        
        .stat-label {{
            font-size: 11px;
            text-transform: uppercase;
            letter-spacing: 1px;
            color: #6b7280;
        }}
        
        .container {{
            display: flex;
            height: calc(100vh - 80px);
        }}
        
        .sidebar {{
            width: 320px;
            background: rgba(15, 15, 30, 0.8);
            border-right: 1px solid rgba(139, 92, 246, 0.2);
            padding: 20px;
            overflow-y: auto;
        }}
        
        .sidebar h2 {{
            font-size: 14px;
            text-transform: uppercase;
            letter-spacing: 1.5px;
            color: #818cf8;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 1px solid rgba(139, 92, 246, 0.2);
        }}
        
        .state-list {{
            list-style: none;
        }}
        
        .state-item {{
            padding: 12px 15px;
            margin-bottom: 8px;
            background: rgba(99, 102, 241, 0.05);
            border: 1px solid rgba(99, 102, 241, 0.2);
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.2s ease;
        }}
        
        .state-item:hover {{
            background: rgba(99, 102, 241, 0.15);
            border-color: rgba(99, 102, 241, 0.4);
            transform: translateX(4px);
        }}
        
        .state-item.active {{
            background: rgba(139, 92, 246, 0.2);
            border-color: #8b5cf6;
        }}
        
        .state-name {{
            font-weight: 600;
            color: #e0e0e0;
            margin-bottom: 4px;
        }}
        
        .state-meta {{
            font-size: 11px;
            color: #6b7280;
        }}
        
        .canvas-container {{
            flex: 1;
            position: relative;
            overflow: hidden;
        }}
        
        #mapCanvas {{
            width: 100%;
            height: 100%;
            cursor: grab;
        }}
        
        #mapCanvas:active {{
            cursor: grabbing;
        }}
        
        .tooltip {{
            position: absolute;
            background: rgba(20, 20, 40, 0.95);
            border: 1px solid rgba(139, 92, 246, 0.4);
            border-radius: 10px;
            padding: 15px;
            pointer-events: none;
            opacity: 0;
            transition: opacity 0.2s ease;
            max-width: 300px;
            box-shadow: 0 10px 40px rgba(0, 0, 0, 0.5);
            z-index: 1000;
        }}
        
        .tooltip.visible {{
            opacity: 1;
        }}
        
        .tooltip h3 {{
            color: #818cf8;
            margin-bottom: 8px;
            font-size: 14px;
        }}
        
        .tooltip p {{
            font-size: 12px;
            color: #9ca3af;
            margin-bottom: 4px;
        }}
        
        .controls {{
            position: absolute;
            bottom: 20px;
            right: 20px;
            display: flex;
            flex-direction: column;
            gap: 10px;
        }}
        
        .control-btn {{
            width: 44px;
            height: 44px;
            border-radius: 10px;
            border: 1px solid rgba(139, 92, 246, 0.3);
            background: rgba(20, 20, 40, 0.8);
            color: #818cf8;
            font-size: 20px;
            cursor: pointer;
            transition: all 0.2s ease;
            display: flex;
            align-items: center;
            justify-content: center;
        }}
        
        .control-btn:hover {{
            background: rgba(139, 92, 246, 0.2);
            border-color: #8b5cf6;
            transform: scale(1.05);
        }}
        
        .legend {{
            position: absolute;
            bottom: 20px;
            left: 20px;
            background: rgba(20, 20, 40, 0.9);
            border: 1px solid rgba(139, 92, 246, 0.3);
            border-radius: 10px;
            padding: 15px;
        }}
        
        .legend h4 {{
            font-size: 12px;
            color: #818cf8;
            margin-bottom: 10px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        
        .legend-item {{
            display: flex;
            align-items: center;
            gap: 10px;
            font-size: 12px;
            color: #9ca3af;
            margin-bottom: 6px;
        }}
        
        .legend-dot {{
            width: 12px;
            height: 12px;
            border-radius: 50%;
        }}
        
        .legend-dot.root {{
            background: linear-gradient(135deg, #8b5cf6, #6366f1);
        }}
        
        .legend-dot.state {{
            background: linear-gradient(135deg, #06b6d4, #3b82f6);
        }}
        
        .legend-line {{
            width: 20px;
            height: 2px;
            background: linear-gradient(90deg, #8b5cf6, #06b6d4);
        }}
        
        @keyframes pulse {{
            0%, 100% {{ transform: scale(1); opacity: 1; }}
            50% {{ transform: scale(1.1); opacity: 0.8; }}
        }}
        
        @keyframes dash {{
            to {{ stroke-dashoffset: -20; }}
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🗺️ {app_name.title()} - fDOM State Map</h1>
        <div class="stats">
            <div class="stat">
                <div class="stat-value">{len(self.nodes)}</div>
                <div class="stat-label">States</div>
            </div>
            <div class="stat">
                <div class="stat-value">{len(self.edges)}</div>
                <div class="stat-label">Transitions</div>
            </div>
            <div class="stat">
                <div class="stat-value">{stats.get('total_nodes', 0)}</div>
                <div class="stat-label">Elements</div>
            </div>
            <div class="stat">
                <div class="stat-value">{stats.get('pending_nodes', 0)}</div>
                <div class="stat-label">Pending</div>
            </div>
        </div>
    </div>
    
    <div class="container">
        <div class="sidebar">
            <h2>📍 States</h2>
            <ul class="state-list" id="stateList">
            </ul>
        </div>
        
        <div class="canvas-container">
            <canvas id="mapCanvas"></canvas>
            
            <div class="tooltip" id="tooltip">
                <h3 id="tooltipTitle"></h3>
                <p id="tooltipContent"></p>
            </div>
            
            <div class="controls">
                <button class="control-btn" id="zoomIn" title="Zoom In">+</button>
                <button class="control-btn" id="zoomOut" title="Zoom Out">−</button>
                <button class="control-btn" id="resetView" title="Reset View">⟲</button>
            </div>
            
            <div class="legend">
                <h4>Legend</h4>
                <div class="legend-item">
                    <div class="legend-dot root"></div>
                    <span>Root State</span>
                </div>
                <div class="legend-item">
                    <div class="legend-dot state"></div>
                    <span>Child State</span>
                </div>
                <div class="legend-item">
                    <div class="legend-line"></div>
                    <span>Navigation Edge</span>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        // Data from Python
        const nodes = {json.dumps(nodes_js)};
        const edges = {json.dumps(edges_js)};
        
        // Canvas setup
        const canvas = document.getElementById('mapCanvas');
        const ctx = canvas.getContext('2d');
        const tooltip = document.getElementById('tooltip');
        const tooltipTitle = document.getElementById('tooltipTitle');
        const tooltipContent = document.getElementById('tooltipContent');
        
        // View state
        let scale = 1;
        let offsetX = 0;
        let offsetY = 0;
        let isDragging = false;
        let lastMouseX = 0;
        let lastMouseY = 0;
        let selectedNode = null;
        let hoveredNode = null;
        let animationFrame = 0;
        
        // Resize canvas
        function resizeCanvas() {{
            canvas.width = canvas.parentElement.clientWidth;
            canvas.height = canvas.parentElement.clientHeight;
            draw();
        }}
        window.addEventListener('resize', resizeCanvas);
        resizeCanvas();
        
        // Center view on initial load
        function centerView() {{
            if (nodes.length > 0) {{
                let minX = Infinity, maxX = -Infinity;
                let minY = Infinity, maxY = -Infinity;
                
                nodes.forEach(node => {{
                    minX = Math.min(minX, node.x);
                    maxX = Math.max(maxX, node.x);
                    minY = Math.min(minY, node.y);
                    maxY = Math.max(maxY, node.y);
                }});
                
                const graphWidth = maxX - minX + 200;
                const graphHeight = maxY - minY + 200;
                const centerX = (minX + maxX) / 2;
                const centerY = (minY + maxY) / 2;
                
                scale = Math.min(
                    canvas.width / graphWidth,
                    canvas.height / graphHeight,
                    1.5
                ) * 0.8;
                
                offsetX = canvas.width / 2 - centerX * scale;
                offsetY = canvas.height / 2 - centerY * scale;
                
                draw();
            }}
        }}
        setTimeout(centerView, 100);
        
        // Transform functions
        function toCanvasX(x) {{ return x * scale + offsetX; }}
        function toCanvasY(y) {{ return y * scale + offsetY; }}
        function fromCanvasX(x) {{ return (x - offsetX) / scale; }}
        function fromCanvasY(y) {{ return (y - offsetY) / scale; }}
        
        // Draw function
        function draw() {{
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            
            // Draw grid
            ctx.strokeStyle = 'rgba(99, 102, 241, 0.05)';
            ctx.lineWidth = 1;
            const gridSize = 50 * scale;
            const startX = offsetX % gridSize;
            const startY = offsetY % gridSize;
            
            for (let x = startX; x < canvas.width; x += gridSize) {{
                ctx.beginPath();
                ctx.moveTo(x, 0);
                ctx.lineTo(x, canvas.height);
                ctx.stroke();
            }}
            for (let y = startY; y < canvas.height; y += gridSize) {{
                ctx.beginPath();
                ctx.moveTo(0, y);
                ctx.lineTo(canvas.width, y);
                ctx.stroke();
            }}
            
            // Draw edges
            edges.forEach(edge => {{
                const fromNode = nodes.find(n => n.id === edge.from);
                const toNode = nodes.find(n => n.id === edge.to);
                
                if (fromNode && toNode) {{
                    const x1 = toCanvasX(fromNode.x);
                    const y1 = toCanvasY(fromNode.y);
                    const x2 = toCanvasX(toNode.x);
                    const y2 = toCanvasY(toNode.y);
                    
                    // Draw curved line
                    const midX = (x1 + x2) / 2;
                    const midY = (y1 + y2) / 2;
                    const dx = x2 - x1;
                    const dy = y2 - y1;
                    const cx = midX - dy * 0.2;
                    const cy = midY + dx * 0.2;
                    
                    // Gradient
                    const gradient = ctx.createLinearGradient(x1, y1, x2, y2);
                    gradient.addColorStop(0, 'rgba(139, 92, 246, 0.6)');
                    gradient.addColorStop(1, 'rgba(6, 182, 212, 0.6)');
                    
                    ctx.beginPath();
                    ctx.moveTo(x1, y1);
                    ctx.quadraticCurveTo(cx, cy, x2, y2);
                    ctx.strokeStyle = gradient;
                    ctx.lineWidth = 2 * scale;
                    ctx.stroke();
                    
                    // Arrow head
                    const angle = Math.atan2(y2 - cy, x2 - cx);
                    const arrowSize = 10 * scale;
                    ctx.beginPath();
                    ctx.moveTo(x2, y2);
                    ctx.lineTo(
                        x2 - arrowSize * Math.cos(angle - Math.PI / 6),
                        y2 - arrowSize * Math.sin(angle - Math.PI / 6)
                    );
                    ctx.moveTo(x2, y2);
                    ctx.lineTo(
                        x2 - arrowSize * Math.cos(angle + Math.PI / 6),
                        y2 - arrowSize * Math.sin(angle + Math.PI / 6)
                    );
                    ctx.strokeStyle = 'rgba(6, 182, 212, 0.8)';
                    ctx.stroke();
                    
                    // Edge label
                    if (scale > 0.6) {{
                        ctx.font = `${{10 * scale}}px JetBrains Mono, monospace`;
                        ctx.fillStyle = 'rgba(156, 163, 175, 0.7)';
                        ctx.textAlign = 'center';
                        ctx.fillText(edge.trigger, cx, cy - 8 * scale);
                    }}
                }}
            }});
            
            // Draw nodes
            nodes.forEach(node => {{
                const x = toCanvasX(node.x);
                const y = toCanvasY(node.y);
                const radius = (node.isRoot ? 35 : 25 + Math.min(node.elements / 5, 15)) * scale;
                
                // Glow effect
                const gradient = ctx.createRadialGradient(x, y, 0, x, y, radius * 2);
                if (node.isRoot) {{
                    gradient.addColorStop(0, 'rgba(139, 92, 246, 0.3)');
                    gradient.addColorStop(1, 'rgba(139, 92, 246, 0)');
                }} else {{
                    gradient.addColorStop(0, 'rgba(6, 182, 212, 0.2)');
                    gradient.addColorStop(1, 'rgba(6, 182, 212, 0)');
                }}
                ctx.beginPath();
                ctx.arc(x, y, radius * 2, 0, Math.PI * 2);
                ctx.fillStyle = gradient;
                ctx.fill();
                
                // Node circle
                ctx.beginPath();
                ctx.arc(x, y, radius, 0, Math.PI * 2);
                
                const nodeGradient = ctx.createLinearGradient(x - radius, y - radius, x + radius, y + radius);
                if (node.isRoot) {{
                    nodeGradient.addColorStop(0, '#8b5cf6');
                    nodeGradient.addColorStop(1, '#6366f1');
                }} else {{
                    nodeGradient.addColorStop(0, '#06b6d4');
                    nodeGradient.addColorStop(1, '#3b82f6');
                }}
                ctx.fillStyle = nodeGradient;
                ctx.fill();
                
                // Border
                ctx.strokeStyle = hoveredNode === node.id ? '#ffffff' : 'rgba(255, 255, 255, 0.2)';
                ctx.lineWidth = hoveredNode === node.id ? 3 * scale : 1.5 * scale;
                ctx.stroke();
                
                // Label
                ctx.font = `bold ${{12 * scale}}px JetBrains Mono, monospace`;
                ctx.fillStyle = '#ffffff';
                ctx.textAlign = 'center';
                ctx.textBaseline = 'middle';
                ctx.fillText(node.label, x, y);
                
                // Element count badge
                if (scale > 0.5) {{
                    const badgeX = x + radius * 0.7;
                    const badgeY = y - radius * 0.7;
                    ctx.beginPath();
                    ctx.arc(badgeX, badgeY, 12 * scale, 0, Math.PI * 2);
                    ctx.fillStyle = '#1e1e2e';
                    ctx.fill();
                    ctx.strokeStyle = 'rgba(139, 92, 246, 0.5)';
                    ctx.lineWidth = 1;
                    ctx.stroke();
                    
                    ctx.font = `${{9 * scale}}px JetBrains Mono`;
                    ctx.fillStyle = '#818cf8';
                    ctx.fillText(node.elements.toString(), badgeX, badgeY);
                }}
            }});
            
            animationFrame++;
            requestAnimationFrame(draw);
        }}
        
        // Event handlers
        canvas.addEventListener('mousedown', (e) => {{
            isDragging = true;
            lastMouseX = e.clientX;
            lastMouseY = e.clientY;
            canvas.style.cursor = 'grabbing';
        }});
        
        canvas.addEventListener('mousemove', (e) => {{
            if (isDragging) {{
                offsetX += e.clientX - lastMouseX;
                offsetY += e.clientY - lastMouseY;
                lastMouseX = e.clientX;
                lastMouseY = e.clientY;
            }} else {{
                // Check for node hover
                const rect = canvas.getBoundingClientRect();
                const mouseX = fromCanvasX(e.clientX - rect.left);
                const mouseY = fromCanvasY(e.clientY - rect.top);
                
                hoveredNode = null;
                nodes.forEach(node => {{
                    const dist = Math.sqrt(Math.pow(mouseX - node.x, 2) + Math.pow(mouseY - node.y, 2));
                    const radius = node.isRoot ? 35 : 25 + Math.min(node.elements / 5, 15);
                    
                    if (dist < radius) {{
                        hoveredNode = node.id;
                        
                        // Show tooltip
                        tooltip.classList.add('visible');
                        tooltipTitle.textContent = node.id;
                        tooltipContent.innerHTML = `
                            <strong>Elements:</strong> ${{node.elements}}<br>
                            <strong>Parent:</strong> ${{node.parent || 'None'}}<br>
                            <strong>Root:</strong> ${{node.isRoot ? 'Yes' : 'No'}}
                        `;
                        tooltip.style.left = (e.clientX + 15) + 'px';
                        tooltip.style.top = (e.clientY + 15) + 'px';
                    }}
                }});
                
                if (!hoveredNode) {{
                    tooltip.classList.remove('visible');
                }}
                
                canvas.style.cursor = hoveredNode ? 'pointer' : 'grab';
            }}
        }});
        
        canvas.addEventListener('mouseup', () => {{
            isDragging = false;
            canvas.style.cursor = hoveredNode ? 'pointer' : 'grab';
        }});
        
        canvas.addEventListener('wheel', (e) => {{
            e.preventDefault();
            const rect = canvas.getBoundingClientRect();
            const mouseX = e.clientX - rect.left;
            const mouseY = e.clientY - rect.top;
            
            const zoomFactor = e.deltaY > 0 ? 0.9 : 1.1;
            const newScale = Math.max(0.2, Math.min(3, scale * zoomFactor));
            
            // Zoom toward mouse position
            offsetX = mouseX - (mouseX - offsetX) * (newScale / scale);
            offsetY = mouseY - (mouseY - offsetY) * (newScale / scale);
            scale = newScale;
        }});
        
        // Control buttons
        document.getElementById('zoomIn').addEventListener('click', () => {{
            scale = Math.min(3, scale * 1.2);
        }});
        
        document.getElementById('zoomOut').addEventListener('click', () => {{
            scale = Math.max(0.2, scale * 0.8);
        }});
        
        document.getElementById('resetView').addEventListener('click', centerView);
        
        // Populate state list
        const stateList = document.getElementById('stateList');
        nodes.forEach(node => {{
            const li = document.createElement('li');
            li.className = 'state-item' + (node.isRoot ? ' root' : '');
            li.innerHTML = `
                <div class="state-name">${{node.isRoot ? '🏠 ' : '📄 '}}${{node.id}}</div>
                <div class="state-meta">${{node.elements}} elements | ${{node.parent ? 'from ' + node.parent : 'root state'}}</div>
            `;
            li.addEventListener('click', () => {{
                // Center on node
                offsetX = canvas.width / 2 - node.x * scale;
                offsetY = canvas.height / 2 - node.y * scale;
                
                // Highlight
                document.querySelectorAll('.state-item').forEach(el => el.classList.remove('active'));
                li.classList.add('active');
            }});
            stateList.appendChild(li);
        }});
    </script>
</body>
</html>'''
        
        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html)
            print(f"✅ MAP visualization saved to: {output_path}")
        
        return html
    
    def generate_mermaid(self) -> str:
        """Generate Mermaid diagram syntax for the state graph"""
        lines = ["graph TD"]
        
        # Add styling
        lines.append("    classDef root fill:#8b5cf6,stroke:#6366f1,color:#fff")
        lines.append("    classDef state fill:#06b6d4,stroke:#3b82f6,color:#fff")
        
        # Add nodes
        for node in self.nodes:
            shape = f"(({node.label}))" if node.is_root else f"[{node.label}]"
            lines.append(f"    {node.id}{shape}")
        
        # Add edges
        for edge in self.edges:
            lines.append(f"    {edge.from_state} -->|{edge.trigger_element}| {edge.to_state}")
        
        # Apply classes
        for node in self.nodes:
            cls = "root" if node.is_root else "state"
            lines.append(f"    class {node.id} {cls}")
        
        return "\n".join(lines)


def generate_map_for_app(app_name: str, output_dir: str = None) -> str:
    """Generate MAP visualization for an app's fDOM"""
    
    base_path = Path(__file__).parent.parent / "apps"
    fdom_path = base_path / app_name / "fdom.json"
    
    if not fdom_path.exists():
        print(f"❌ fDOM not found for app: {app_name}")
        return None
    
    generator = FDOMMapGenerator(str(fdom_path))
    
    output_dir = output_dir or str(base_path / app_name)
    output_path = os.path.join(output_dir, "fdom_map.html")
    
    html = generator.generate_html(output_path, f"{app_name.title()} State Map")
    
    return output_path


# Test
if __name__ == "__main__":
    print("🗺️ Generating fDOM MAP visualization...")
    
    # Try notepad first
    result = generate_map_for_app("notepad")
    if result:
        print(f"✅ MAP saved to: {result}")
    else:
        print("⚠️ Notepad fDOM not found, trying blender...")
        result = generate_map_for_app("blender")
        if result:
            print(f"✅ MAP saved to: {result}")

