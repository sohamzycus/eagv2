# core/graph_adapter.py - Graph Adapter for Frontend Visualization
# S20: Essential for Frontend Visualization

import json
from typing import Dict, List, Any, Optional
from datetime import datetime


class GraphAdapter:
    """
    Adapter to convert NetworkX graph to frontend-compatible format.
    
    This is essential for UI visualization - converts the internal
    NetworkX DiGraph structure to a format consumable by React/Vue frontends.
    """
    
    @staticmethod
    def to_frontend_format(context) -> Dict[str, Any]:
        """
        Convert ExecutionContextManager to frontend-friendly format.
        
        Returns:
        {
            "session_id": "...",
            "query": "...",
            "nodes": [...],
            "edges": [...],
            "status": "running|completed|failed",
            "progress": 0.0-1.0,
            "current_phase": "Planning|Executing|Formatting",
            "globals": {...}
        }
        """
        plan_graph = context.plan_graph
        
        # Build nodes list
        nodes = []
        completed_count = 0
        total_count = 0
        
        for node_id, node_data in plan_graph.nodes(data=True):
            if node_id == "ROOT":
                continue
            
            total_count += 1
            status = node_data.get('status', 'pending')
            
            if status == 'completed':
                completed_count += 1
            
            nodes.append({
                "id": node_id,
                "agent": node_data.get('agent', 'Unknown'),
                "description": node_data.get('description', '')[:100],
                "status": status,
                "has_output": node_data.get('output') is not None,
                "has_error": node_data.get('error') is not None,
                "started_at": node_data.get('started_at'),
                "completed_at": node_data.get('completed_at')
            })
        
        # Build edges list
        edges = []
        for source, target in plan_graph.edges():
            edges.append({
                "source": source,
                "target": target
            })
        
        # Calculate progress
        progress = completed_count / total_count if total_count > 0 else 0.0
        
        # Determine current phase
        running_nodes = [n for n in nodes if n['status'] == 'running']
        if running_nodes:
            current_agent = running_nodes[0]['agent']
            if 'Planner' in current_agent:
                current_phase = "Planning"
            elif 'Formatter' in current_agent:
                current_phase = "Formatting"
            else:
                current_phase = "Executing"
        elif progress >= 1.0:
            current_phase = "Complete"
        else:
            current_phase = "Pending"
        
        # Overall status
        failed_nodes = [n for n in nodes if n['status'] == 'failed']
        if failed_nodes:
            overall_status = "failed"
        elif progress >= 1.0:
            overall_status = "completed"
        elif running_nodes:
            overall_status = "running"
        else:
            overall_status = "pending"
        
        return {
            "session_id": plan_graph.graph.get('session_id', ''),
            "query": plan_graph.graph.get('original_query', ''),
            "nodes": nodes,
            "edges": edges,
            "status": overall_status,
            "progress": round(progress, 2),
            "current_phase": current_phase,
            "globals": plan_graph.graph.get('globals_schema', {}),
            "timestamp": datetime.now().isoformat()
        }
    
    @staticmethod
    def to_mermaid(context) -> str:
        """
        Convert graph to Mermaid diagram format for markdown visualization.
        
        Example output:
        ```mermaid
        graph TD
            ROOT[Query] --> T001
            T001[BrowserAgent: Search] --> T002
            T002[CoderAgent: Analyze] --> T003
        ```
        """
        plan_graph = context.plan_graph
        lines = ["graph TD"]
        
        # Add nodes
        for node_id, node_data in plan_graph.nodes(data=True):
            agent = node_data.get('agent', 'System')
            desc = node_data.get('description', '')[:30].replace('"', "'")
            status = node_data.get('status', 'pending')
            
            # Status styling
            if status == 'completed':
                style = ":::done"
            elif status == 'running':
                style = ":::active"
            elif status == 'failed':
                style = ":::error"
            else:
                style = ""
            
            if node_id == "ROOT":
                lines.append(f'    ROOT["{desc[:20]}..."]{style}')
            else:
                lines.append(f'    {node_id}["{agent}: {desc}"]{style}')
        
        # Add edges
        for source, target in plan_graph.edges():
            lines.append(f"    {source} --> {target}")
        
        # Add styles
        lines.extend([
            "",
            "    classDef done fill:#90EE90,stroke:#228B22;",
            "    classDef active fill:#FFD700,stroke:#FFA500;",
            "    classDef error fill:#FF6B6B,stroke:#DC143C;"
        ])
        
        return "\n".join(lines)
    
    @staticmethod
    def get_step_details(context, step_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific step."""
        if step_id not in context.plan_graph.nodes:
            return None
        
        node_data = dict(context.plan_graph.nodes[step_id])
        
        # Get predecessors and successors
        predecessors = list(context.plan_graph.predecessors(step_id))
        successors = list(context.plan_graph.successors(step_id))
        
        return {
            "id": step_id,
            "agent": node_data.get('agent'),
            "description": node_data.get('description'),
            "agent_prompt": node_data.get('agent_prompt'),
            "status": node_data.get('status'),
            "reads": node_data.get('reads', []),
            "writes": node_data.get('writes', []),
            "output": node_data.get('output'),
            "error": node_data.get('error'),
            "iterations": node_data.get('iterations', []),
            "predecessors": predecessors,
            "successors": successors,
            "timing": {
                "started_at": node_data.get('started_at'),
                "completed_at": node_data.get('completed_at'),
                "failed_at": node_data.get('failed_at')
            }
        }
