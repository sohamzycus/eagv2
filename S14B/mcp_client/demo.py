#!/usr/bin/env python3
"""
fDOM MCP Client Demo
Demonstrates the complete pipeline:
1. Load fDOM data
2. Connect to Ollama
3. Execute 5-step computer tasks
4. Run 50-iteration exploration
5. Generate MAP visualization

Usage:
    python -m mcp_client.demo --app notepad --task "Open file menu"
    python -m mcp_client.demo --app notepad --explore --iterations 50
    python -m mcp_client.demo --app notepad --generate-map
"""

import argparse
import asyncio
import json
import sys
import os
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from mcp_client.ollama_client import OllamaClient
from mcp_client.mcp_server import MCPServer, FDOMContext
from mcp_client.fdom_map import FDOMMapGenerator, generate_map_for_app
from mcp_client.task_executor import TaskExecutor, ExplorationExecutor


def print_banner():
    """Print demo banner"""
    banner = """
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║     🤖 fDOM MCP Client - Ollama Computer Control Agent 🤖       ║
║                                                                  ║
║     • Load fDOM State Machine                                    ║
║     • Plan Tasks with Ollama LLM                                 ║
║     • Execute 5-Step Computer Tasks                              ║
║     • Run 50-Iteration Explorations                              ║
║     • Visualize State Graphs (MAP APP)                           ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
"""
    print(banner)


def check_prerequisites():
    """Check that all prerequisites are met"""
    print("\n📋 Checking Prerequisites...")
    
    all_good = True
    
    # Check Ollama
    print("\n1. Checking Ollama:")
    client = OllamaClient()
    status = client.check_ollama_status()
    
    if status["status"] == "online":
        print(f"   ✅ Ollama is running")
        print(f"   📦 Available models: {', '.join(status['models'][:5])}")
    else:
        print(f"   ⚠️ Ollama is offline: {status.get('error', 'Unknown')}")
        print(f"   💡 Start Ollama: ollama serve")
        all_good = False
    
    # Check apps directory
    print("\n2. Checking fDOM data:")
    apps_dir = Path(__file__).parent.parent / "apps"
    
    if apps_dir.exists():
        apps = [d.name for d in apps_dir.iterdir() if d.is_dir() and (d / "fdom.json").exists()]
        if apps:
            print(f"   ✅ Found {len(apps)} apps with fDOM data")
            print(f"   📱 Available: {', '.join(apps)}")
        else:
            print(f"   ⚠️ No fDOM data found in {apps_dir}")
            all_good = False
    else:
        print(f"   ⚠️ Apps directory not found: {apps_dir}")
        all_good = False
    
    return all_good


def list_available_apps():
    """List all available apps with fDOM data"""
    apps_dir = Path(__file__).parent.parent / "apps"
    
    if not apps_dir.exists():
        print("❌ Apps directory not found")
        return []
    
    apps = []
    for app_dir in apps_dir.iterdir():
        if app_dir.is_dir():
            fdom_path = app_dir / "fdom.json"
            if fdom_path.exists():
                try:
                    with open(fdom_path, 'r') as f:
                        data = json.load(f)
                    
                    stats = data.get("exploration_stats", {})
                    apps.append({
                        "name": app_dir.name,
                        "states": len(data.get("states", {})),
                        "edges": len(data.get("edges", [])),
                        "total_nodes": stats.get("total_nodes", 0),
                        "pending": stats.get("pending_nodes", 0)
                    })
                except Exception as e:
                    print(f"   ⚠️ Error loading {app_dir.name}: {e}")
    
    if apps:
        print("\n📱 Available Apps:")
        print("-" * 60)
        for app in apps:
            print(f"   {app['name']:15} | States: {app['states']:3} | Nodes: {app['total_nodes']:4} | Pending: {app['pending']:4}")
        print("-" * 60)
    
    return [a["name"] for a in apps]


async def run_5_step_task(app_name: str, task: str, dry_run: bool = False):
    """Run a 5-step task"""
    
    print(f"\n🎯 Running 5-Step Task")
    print(f"📱 App: {app_name}")
    print(f"📝 Task: {task}")
    print(f"🏃 Mode: {'Dry Run' if dry_run else 'Execute'}\n")
    
    executor = TaskExecutor(app_name)
    
    # Check Ollama
    status = executor.check_ollama()
    if status["status"] != "online":
        print(f"⚠️ Ollama is not available. Running in simulation mode.")
    
    result = await executor.execute_task(task, max_steps=5, dry_run=dry_run)
    
    # Save results
    output_dir = Path(__file__).parent.parent / "outputs"
    output_dir.mkdir(exist_ok=True)
    
    result_path = output_dir / f"task_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(result_path, 'w') as f:
        json.dump(result.to_dict(), f, indent=2)
    
    print(f"\n💾 Results saved to: {result_path}")
    
    return result


async def run_50_iterations(app_name: str, iterations: int = 50, use_ollama: bool = True):
    """Run 50 iterations of exploration"""
    
    print(f"\n🔍 Running {iterations}-Iteration Exploration")
    print(f"📱 App: {app_name}")
    print(f"🧠 Ollama Guidance: {'Enabled' if use_ollama else 'Disabled'}\n")
    
    executor = ExplorationExecutor(app_name)
    
    summary = await executor.run_exploration(
        max_iterations=iterations,
        use_ollama_guidance=use_ollama
    )
    
    # Save results
    output_dir = Path(__file__).parent.parent / "outputs"
    output_dir.mkdir(exist_ok=True)
    
    result_path = output_dir / f"exploration_{app_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    full_results = {
        "summary": summary,
        "iterations": executor.get_results()
    }
    
    with open(result_path, 'w') as f:
        json.dump(full_results, f, indent=2)
    
    print(f"\n💾 Results saved to: {result_path}")
    
    return summary


def generate_map(app_name: str):
    """Generate MAP visualization for an app"""
    
    print(f"\n🗺️ Generating MAP Visualization")
    print(f"📱 App: {app_name}\n")
    
    output_path = generate_map_for_app(app_name)
    
    if output_path:
        print(f"\n✅ MAP generated: {output_path}")
        print(f"💡 Open in browser to view interactive state graph")
    else:
        print(f"❌ Failed to generate MAP for {app_name}")
    
    return output_path


async def interactive_demo(app_name: str):
    """Run an interactive demo session"""
    
    print("\n🎮 Interactive Demo Mode")
    print("=" * 50)
    print("Commands:")
    print("  task <description>  - Run a 5-step task")
    print("  explore <n>         - Explore for n iterations")
    print("  map                 - Generate MAP visualization")
    print("  state               - Show current state info")
    print("  elements            - List available elements")
    print("  quit                - Exit")
    print("=" * 50)
    
    # Initialize components
    context = FDOMContext(app_name)
    mcp = MCPServer(context)
    
    while True:
        try:
            user_input = input("\n> ").strip()
            
            if not user_input:
                continue
            
            parts = user_input.split(maxsplit=1)
            cmd = parts[0].lower()
            arg = parts[1] if len(parts) > 1 else ""
            
            if cmd == "quit" or cmd == "exit":
                print("👋 Goodbye!")
                break
            
            elif cmd == "task":
                if not arg:
                    print("Usage: task <description>")
                    continue
                await run_5_step_task(app_name, arg, dry_run=False)
            
            elif cmd == "explore":
                iterations = int(arg) if arg.isdigit() else 10
                await run_50_iterations(app_name, iterations)
            
            elif cmd == "map":
                generate_map(app_name)
            
            elif cmd == "state":
                result = await mcp.handle_tool_call("get_current_state")
                print(json.dumps(result, indent=2))
            
            elif cmd == "elements":
                result = await mcp.handle_tool_call("get_elements")
                elements = result.get("elements", [])[:15]
                print(f"\n📋 Elements in {context.current_state}:")
                for e in elements:
                    print(f"   • {e['id']}: {e['name']} ({e['type']})")
            
            else:
                print(f"Unknown command: {cmd}")
        
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"Error: {e}")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="fDOM MCP Client - Ollama-powered Computer Control Agent"
    )
    
    parser.add_argument("--app", type=str, default="notepad",
                       help="App name to work with (default: notepad)")
    parser.add_argument("--task", type=str,
                       help="Run a 5-step task with this description")
    parser.add_argument("--explore", action="store_true",
                       help="Run exploration mode")
    parser.add_argument("--iterations", type=int, default=50,
                       help="Number of exploration iterations (default: 50)")
    parser.add_argument("--generate-map", action="store_true",
                       help="Generate MAP visualization")
    parser.add_argument("--interactive", action="store_true",
                       help="Run interactive demo mode")
    parser.add_argument("--list-apps", action="store_true",
                       help="List available apps with fDOM data")
    parser.add_argument("--check", action="store_true",
                       help="Check prerequisites")
    parser.add_argument("--dry-run", action="store_true",
                       help="Plan but don't execute tasks")
    parser.add_argument("--no-ollama", action="store_true",
                       help="Disable Ollama guidance (use simple selection)")
    
    args = parser.parse_args()
    
    print_banner()
    
    if args.check:
        check_prerequisites()
        return
    
    if args.list_apps:
        list_available_apps()
        return
    
    if args.generate_map:
        generate_map(args.app)
        return
    
    if args.interactive:
        asyncio.run(interactive_demo(args.app))
        return
    
    if args.task:
        asyncio.run(run_5_step_task(args.app, args.task, dry_run=args.dry_run))
        return
    
    if args.explore:
        asyncio.run(run_50_iterations(
            args.app, 
            iterations=args.iterations,
            use_ollama=not args.no_ollama
        ))
        return
    
    # Default: show help
    parser.print_help()
    print("\n📝 Quick Examples:")
    print("  python -m mcp_client.demo --app notepad --task 'Open file menu'")
    print("  python -m mcp_client.demo --app notepad --explore --iterations 50")
    print("  python -m mcp_client.demo --app notepad --generate-map")
    print("  python -m mcp_client.demo --interactive")


if __name__ == "__main__":
    main()

