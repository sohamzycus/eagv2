#!/usr/bin/env python3
"""
S15_NewArch Agent System with Gradio UI
- Tracks execution flow visually
- Shows DAG, logs, and results
"""

import asyncio
import sys
import os
from pathlib import Path
from datetime import datetime
import threading
import queue

# Add to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import gradio as gr

# Global state for UI updates
execution_logs = []
execution_dag = ""
is_running = False

def add_log(msg: str):
    """Add a log entry with timestamp"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    execution_logs.append(f"[{timestamp}] {msg}")
    if len(execution_logs) > 100:
        execution_logs.pop(0)

def run_agent_in_thread(query: str, result_queue: queue.Queue):
    """Run agent in a separate thread with its own event loop"""
    
    async def async_run():
        global execution_dag, is_running
        
        from core.loop import AgentLoop4
        from mcp_servers.multi_mcp import MultiMCP
        from core.utils import set_log_callback
        
        set_log_callback(add_log)
        add_log("🚀 Starting MCP servers...")
        
        multi_mcp = MultiMCP()
        
        try:
            await multi_mcp.start()
            add_log(f"✅ MCP connected: {list(multi_mcp.sessions.keys())}")
            
            agent_loop = AgentLoop4(multi_mcp=multi_mcp)
            add_log(f"📝 Query: {query}")
            
            context = await agent_loop.run(
                query=query,
                file_manifest=[],
                globals_schema={},
                uploaded_files=[]
            )
            
            if context:
                summary = context.get_execution_summary()
                add_log(f"✅ Completed {len(summary.get('completed_steps', []))} steps")
                
                # Build DAG visualization
                dag_lines = ["\n## 📊 Execution DAG\n"]
                for step in summary.get('completed_steps', []):
                    dag_lines.append(f"✅ {step}")
                for step in summary.get('failed_steps', []):
                    dag_lines.append(f"❌ {step}")
                execution_dag = "\n".join(dag_lines)
                
                # Get result
                gs = summary.get('globals_schema', {})
                result = ""
                for key in ['final_answer', 'formatted_report', 'fallback_markdown', 'summary', 'result']:
                    if key in gs:
                        result = str(gs[key])
                        break
                
                if not result:
                    for k, v in reversed(list(gs.items())):
                        if v and not k.startswith('_'):
                            result = str(v)[:3000]
                            break
                
                result_queue.put(("success", result or "Completed successfully"))
            else:
                result_queue.put(("error", "No context returned"))
                
        except Exception as e:
            import traceback
            add_log(f"❌ Error: {e}")
            traceback.print_exc()
            result_queue.put(("error", str(e)))
        finally:
            try:
                await multi_mcp.stop()
            except:
                pass
            set_log_callback(None)
            is_running = False
            add_log("🏁 Execution complete")
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(async_run())
    finally:
        loop.close()


def process_query(query: str):
    """Process a query and yield streaming updates"""
    global execution_logs, execution_dag, is_running
    
    if not query.strip():
        yield "Please enter a query"
        return
    
    execution_logs.clear()
    execution_dag = ""
    is_running = True
    
    result_queue = queue.Queue()
    thread = threading.Thread(target=run_agent_in_thread, args=(query, result_queue))
    thread.start()
    
    # Stream updates
    while thread.is_alive():
        logs_text = "\n".join(execution_logs[-25:])
        yield f"""## 🔄 Running...

```
{logs_text}
```

{execution_dag}
"""
        import time
        time.sleep(0.5)
    
    thread.join()
    
    try:
        status, result = result_queue.get_nowait()
    except:
        status, result = "error", "Unknown error"
    
    logs_text = "\n".join(execution_logs)
    
    yield f"""## ✅ Result

{result}

---

{execution_dag}

<details>
<summary>📋 Full Execution Log ({len(execution_logs)} entries)</summary>

```
{logs_text}
```

</details>
"""


# Create Gradio Interface - Using simple interface instead of Chatbot
with gr.Blocks(title="S15 NewArch Agent") as demo:
    gr.Markdown("""
    # 🤖 S15 NewArch Agent System
    
    **S20 Production Fixes Applied:**
    - ✅ Stringified List Bug Fix
    - ✅ Bootstrap Context (Instant UI feedback)
    - ✅ Final Turn Warning
    - ✅ 3-Strategy Extraction Fallbacks
    - ✅ Web Search (DuckDuckGo)
    - ✅ RAG Search (Local documents)
    
    ---
    
    **Example queries:**
    - 🌐 `What's the latest revenue of Dhurandhar Movie` (Web search)
    - 📚 `Search stored documents about cricket achievements` (RAG)
    """)
    
    with gr.Row():
        query_input = gr.Textbox(
            label="Your Query",
            placeholder="Ask anything... (e.g., 'What is the revenue of Dhurandhar Movie?')",
            scale=4
        )
        submit_btn = gr.Button("🚀 Run Agent", variant="primary", scale=1)
    
    output_box = gr.Markdown(
        label="Execution Output",
        value="*Enter a query and click Run Agent*"
    )
    
    clear_btn = gr.Button("🗑️ Clear")
    
    submit_btn.click(
        process_query,
        inputs=[query_input],
        outputs=[output_box]
    )
    
    query_input.submit(
        process_query,
        inputs=[query_input],
        outputs=[output_box]
    )
    
    clear_btn.click(
        lambda: ("", "*Enter a query and click Run Agent*"),
        outputs=[query_input, output_box]
    )


if __name__ == "__main__":
    print("=" * 60)
    print("🚀 Starting S15 NewArch Agent UI")
    print("=" * 60)
    print("\n📍 Open in browser: http://127.0.0.1:7860\n")
    demo.launch(server_name="127.0.0.1", server_port=7860)
