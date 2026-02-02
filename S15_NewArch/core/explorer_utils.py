# core/explorer_utils.py - File Tree and Explorer Utilities
# S20: Helper utilities for file exploration

import os
from pathlib import Path
from typing import Dict, List, Optional, Any
import json
import mimetypes


def get_file_tree(root_path: str, max_depth: int = 3, include_hidden: bool = False) -> Dict[str, Any]:
    """
    Generate a file tree structure from a directory.
    
    Args:
        root_path: Root directory to explore
        max_depth: Maximum depth to traverse
        include_hidden: Whether to include hidden files (starting with .)
    
    Returns:
        Dictionary representing the file tree
    """
    root = Path(root_path)
    
    def build_tree(path: Path, depth: int) -> Optional[Dict]:
        if depth > max_depth:
            return None
        
        if not include_hidden and path.name.startswith('.'):
            return None
        
        if path.is_file():
            return {
                "name": path.name,
                "type": "file",
                "size": path.stat().st_size,
                "extension": path.suffix,
                "mime_type": mimetypes.guess_type(str(path))[0]
            }
        
        if path.is_dir():
            children = []
            try:
                for child in sorted(path.iterdir()):
                    child_tree = build_tree(child, depth + 1)
                    if child_tree:
                        children.append(child_tree)
            except PermissionError:
                pass
            
            return {
                "name": path.name,
                "type": "directory",
                "children": children,
                "child_count": len(children)
            }
        
        return None
    
    return build_tree(root, 0)


def format_file_tree_text(tree: Dict[str, Any], indent: int = 0) -> str:
    """Format file tree as text with indentation."""
    lines = []
    prefix = "  " * indent
    
    name = tree.get("name", "")
    if tree.get("type") == "directory":
        lines.append(f"{prefix}📁 {name}/")
        for child in tree.get("children", []):
            lines.append(format_file_tree_text(child, indent + 1))
    else:
        size = tree.get("size", 0)
        size_str = format_file_size(size)
        lines.append(f"{prefix}📄 {name} ({size_str})")
    
    return "\n".join(lines)


def format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable format."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"


def get_file_info(file_path: str) -> Dict[str, Any]:
    """Get detailed information about a file."""
    path = Path(file_path)
    
    if not path.exists():
        return {"error": f"File not found: {file_path}"}
    
    stat = path.stat()
    
    return {
        "name": path.name,
        "path": str(path.absolute()),
        "extension": path.suffix,
        "mime_type": mimetypes.guess_type(str(path))[0],
        "size": stat.st_size,
        "size_human": format_file_size(stat.st_size),
        "created": stat.st_ctime,
        "modified": stat.st_mtime,
        "is_file": path.is_file(),
        "is_dir": path.is_dir(),
        "is_readable": os.access(path, os.R_OK),
        "is_writable": os.access(path, os.W_OK)
    }


def find_files_by_extension(root_path: str, extensions: List[str], max_results: int = 100) -> List[Dict[str, Any]]:
    """
    Find files with specific extensions.
    
    Args:
        root_path: Root directory to search
        extensions: List of extensions to match (e.g., ['.py', '.md'])
        max_results: Maximum number of results to return
    
    Returns:
        List of file info dictionaries
    """
    root = Path(root_path)
    results = []
    
    # Normalize extensions
    extensions = [ext.lower() if ext.startswith('.') else f'.{ext.lower()}' for ext in extensions]
    
    for path in root.rglob('*'):
        if path.is_file() and path.suffix.lower() in extensions:
            results.append({
                "name": path.name,
                "path": str(path),
                "relative_path": str(path.relative_to(root)),
                "size": path.stat().st_size,
                "extension": path.suffix
            })
            
            if len(results) >= max_results:
                break
    
    return results


def get_directory_stats(dir_path: str) -> Dict[str, Any]:
    """Get statistics about a directory."""
    root = Path(dir_path)
    
    if not root.is_dir():
        return {"error": f"Not a directory: {dir_path}"}
    
    total_size = 0
    file_count = 0
    dir_count = 0
    extensions = {}
    
    for path in root.rglob('*'):
        if path.is_file():
            file_count += 1
            total_size += path.stat().st_size
            ext = path.suffix.lower() or '(no extension)'
            extensions[ext] = extensions.get(ext, 0) + 1
        elif path.is_dir():
            dir_count += 1
    
    # Sort extensions by count
    top_extensions = sorted(extensions.items(), key=lambda x: x[1], reverse=True)[:10]
    
    return {
        "path": str(root.absolute()),
        "total_size": total_size,
        "total_size_human": format_file_size(total_size),
        "file_count": file_count,
        "directory_count": dir_count,
        "top_extensions": dict(top_extensions)
    }
