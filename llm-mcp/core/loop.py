# core/loop.py

import asyncio
from core.context import AgentContext
from core.session import MultiMCP
from core.strategy import decide_next_action
from modules.perception import extract_perception, PerceptionResult
from modules.action import ToolCallResult, parse_function_call
from modules.memory import MemoryItem
import json


class AgentLoop:
    def __init__(self, user_input: str, dispatcher: MultiMCP):
        self.context = AgentContext(user_input)
        self.mcp = dispatcher
        self.tools = dispatcher.get_all_tools()

    def tool_expects_input(self, tool_name: str) -> bool:
        tool = next((t for t in self.tools if getattr(t, "name", None) == tool_name), None)
        if not tool:
            return False
        parameters = getattr(tool, "parameters", {})
        return list(parameters.keys()) == ["input"]

    
    async def _call_tool_text(self, tool_name: str, arguments: dict) -> str:
        response = await self.mcp.call_tool(tool_name, arguments)
        content_obj = getattr(response, "content", None)
        raw = ""
        if isinstance(content_obj, list):
            parts = []
            for part in content_obj:
                text_val = getattr(part, "text", None)
                if text_val is not None:
                    parts.append(str(text_val))
                    continue
                data_val = getattr(part, "data", None)
                if data_val is not None:
                    try:
                        parts.append(json.dumps(data_val))
                    except Exception:
                        parts.append(str(data_val))
                    continue
                parts.append(str(part))
            raw = "\n".join([p for p in parts if p is not None])
        else:
            text_val = getattr(content_obj, "text", None)
            if text_val is not None:
                raw = str(text_val)
            else:
                data_val = getattr(content_obj, "data", None)
                if data_val is not None:
                    try:
                        raw = json.dumps(data_val)
                    except Exception:
                        raw = str(data_val)
                else:
                    raw = str(response) if content_obj is None else str(content_obj)
        return raw

    def _add_memory(self, tool_name: str, arguments: dict, result_str: str):
        memory_item = MemoryItem(
            text=f"{tool_name}({arguments}) → {result_str}",
            type="tool_output",
            tool_name=tool_name,
            user_query=self.context.user_input,
            tags=[tool_name],
            session_id=self.context.session_id
        )
        self.context.add_memory(memory_item)


    async def run(self) -> str:
        print(f"[agent] Starting session: {self.context.session_id}")

        try:
            max_steps = self.context.agent_profile.max_steps
            query = self.context.user_input

            for step in range(max_steps):
                self.context.step = step
                print(f"[loop] Step {step + 1} of {max_steps}")

                # Fast-path routing BEFORE any LLM calls
                initial_q = (self.context.user_input or "").lower()
                has_fetched = any(m.tool_name == "fetch_task" for m in self.context.memory_trace)
                plan = None
                # If the initial instruction is to fetch inbox, do that first without LLM
                if (not has_fetched) and ("inbox" in initial_q and "fetch" in initial_q):
                    plan = "FUNCTION_CALL: fetch_task"
                else:
                    # If the current query clearly requests the F1 workflow, call it deterministically
                    ql_now = (query or "").lower()
                    has_workflows = any(getattr(t, "name", "") == "process_f1_to_sheet_and_email" for t in self.tools)
                    if has_workflows and ("f1" in ql_now or "formula 1" in ql_now) and ("standing" in ql_now or "standings" in ql_now):
                        # Perform deterministic pipeline: standings → sheet → append → share → email
                        try:
                            rows_raw = await self._call_tool_text("get_f1_standings", {})
                            try:
                                rows = json.loads(rows_raw).get("rows", [])
                            except Exception:
                                rows = []
                            self._add_memory("get_f1_standings", {}, rows_raw)

                            ss_raw = await self._call_tool_text("create_spreadsheet", {"title": "F1 Driver Standings"})
                            ss = {}
                            try:
                                ss = json.loads(ss_raw)
                            except Exception:
                                pass
                            self._add_memory("create_spreadsheet", {"title": "F1 Driver Standings"}, ss_raw)

                            ssid = ss.get("spreadsheetId")
                            ssurl = ss.get("spreadsheetUrl")
                            if ssid and rows:
                                app_raw = await self._call_tool_text("append_values", {"spreadsheet_id": ssid, "values": rows})
                                self._add_memory("append_values", {"spreadsheet_id": ssid, "values": "[rows]"}, app_raw)

                            if ssid:
                                share_raw = await self._call_tool_text("share_file", {"file_id": ssid})
                                self._add_memory("share_file", {"file_id": ssid}, share_raw)

                            email_body = f"Here is the F1 standings sheet: {ssurl or '[no url]'}"
                            email_raw = await self._call_tool_text("send_email", {"subject": "F1 Standings Sheet", "body": email_body})
                            self._add_memory("send_email", {"subject": "F1 Standings Sheet", "body": "[url]"}, email_raw)

                            final_summary = {
                                "sheetUrl": ssurl,
                                "sheetId": ssid,
                                "emailStatus": email_raw,
                            }
                            self.context.final_answer = f"FINAL_ANSWER: {json.dumps(final_summary)}"
                            break
                        except Exception as e:
                            print(f"[pipeline] error: {e}")
                            # Fall back to planned path if pipeline fails
                            plan = None

                if plan is None:
                    # 🧠 Perception (only if we didn't fast-path)
                    perception_raw = await extract_perception(query)

                    # If we did perception, handle its outputs
                    # ✅ Exit cleanly on FINAL_ANSWER
                    # ✅ Handle string outputs safely before trying to parse
                    if isinstance(perception_raw, str):
                        pr_str = perception_raw.strip()
                        
                        # Clean exit if it's a FINAL_ANSWER
                        if pr_str.startswith("FINAL_ANSWER:"):
                            self.context.final_answer = pr_str
                            break

                        # Detect LLM echoing the prompt
                        if "Your last tool produced this result" in pr_str or "Original user task:" in pr_str:
                            print("[perception] ⚠️ LLM likely echoed prompt. No actionable plan.")
                            self.context.final_answer = "FINAL_ANSWER: [no result]"
                            break

                        # Try to decode stringified JSON if it looks valid
                        try:
                            perception_raw = json.loads(pr_str)
                        except json.JSONDecodeError:
                            print("[perception] ⚠️ LLM response was neither valid JSON nor actionable text.")
                            self.context.final_answer = "FINAL_ANSWER: [no result]"
                            break

                    # ✅ Try parsing PerceptionResult
                    if isinstance(perception_raw, PerceptionResult):
                        perception = perception_raw
                    else:
                        try:
                            # Attempt to parse stringified JSON if needed
                            if isinstance(perception_raw, str):
                                perception_raw = json.loads(perception_raw)
                            perception = PerceptionResult(**perception_raw)
                        except Exception as e:
                            print(f"[perception] ⚠️ LLM perception failed: {e}")
                            print(f"[perception] Raw output: {perception_raw}")
                            break

                    print(f"[perception] Intent: {perception.intent}, Hint: {perception.tool_hint}")
                else:
                    perception = PerceptionResult(user_input=query, intent=None, entities=[], tool_hint=None)

                # 💾 Memory Retrieval (skip until we actually have something stored to avoid latency)
                if self.context.memory_trace:
                    retrieved = self.context.memory.retrieve(
                        query=query,
                        top_k=self.context.agent_profile.memory_config["top_k"],
                        type_filter=self.context.agent_profile.memory_config.get("type_filter", None),
                        session_filter=self.context.session_id
                    )
                    print(f"[memory] Retrieved {len(retrieved)} memories")
                else:
                    retrieved = []
                    print("[memory] Skipped (no prior memories)")

                # 📊 Planning (via strategy) with lightweight fallback
                if plan is None:
                    # Deterministic route: if the current query mentions F1 standings, call the workflow tool
                    ql = (query or "").lower()
                    has_workflows = any(getattr(t, "name", "") == "process_f1_to_sheet_and_email" for t in self.tools)
                    if has_workflows and ("f1" in ql or "formula 1" in ql) and ("standing" in ql or "standings" in ql):
                        plan = "FUNCTION_CALL: process_f1_to_sheet_and_email"
                    else:
                        plan = await decide_next_action(
                            context=self.context,
                            perception=perception,
                            memory_items=retrieved,
                            all_tools=self.tools
                        )
                print(f"[plan] {plan}")

                if "FINAL_ANSWER:" in plan:
                    # Optionally extract the final answer portion
                    final_lines = [line for line in plan.splitlines() if line.strip().startswith("FINAL_ANSWER:")]
                    if final_lines:
                        self.context.final_answer = final_lines[-1].strip()
                    else:
                        self.context.final_answer = "FINAL_ANSWER: [result found, but could not extract]"
                    break


                # ⚙️ Tool Execution
                try:
                    tool_name, arguments = parse_function_call(plan)

                    if self.tool_expects_input(tool_name):
                        tool_input = {'input': arguments} if not (isinstance(arguments, dict) and 'input' in arguments) else arguments
                    else:
                        tool_input = arguments

                    response = await self.mcp.call_tool(tool_name, tool_input)

                    # ✅ Safe content parsing: support lists, text/json parts
                    content_obj = getattr(response, "content", None)
                    raw = ""
                    if isinstance(content_obj, list):
                        parts = []
                        for part in content_obj:
                            text_val = getattr(part, "text", None)
                            if text_val is not None:
                                parts.append(str(text_val))
                                continue
                            data_val = getattr(part, "data", None)
                            if data_val is not None:
                                try:
                                    parts.append(json.dumps(data_val))
                                except Exception:
                                    parts.append(str(data_val))
                                continue
                            parts.append(str(part))
                        raw = "\n".join([p for p in parts if p is not None])
                    else:
                        # Single content
                        text_val = getattr(content_obj, "text", None)
                        if text_val is not None:
                            raw = str(text_val)
                        else:
                            data_val = getattr(content_obj, "data", None)
                            if data_val is not None:
                                try:
                                    raw = json.dumps(data_val)
                                except Exception:
                                    raw = str(data_val)
                            else:
                                # Fall back to whole response
                                raw = str(response) if content_obj is None else str(content_obj)
                    try:
                        result_obj = json.loads(raw) if raw.strip().startswith("{") else raw
                    except json.JSONDecodeError:
                        result_obj = raw

                    result_str = result_obj.get("markdown") if isinstance(result_obj, dict) else str(result_obj)
                    print(f"[action] {tool_name} → {result_str}")

                    # 🧠 Add memory
                    memory_item = MemoryItem(
                        text=f"{tool_name}({arguments}) → {result_str}",
                        type="tool_output",
                        tool_name=tool_name,
                        user_query=query,
                        tags=[tool_name],
                        session_id=self.context.session_id
                    )
                    self.context.add_memory(memory_item)

                    # 🔁 Next query
                    # If the workflow tool completed, end early with final answer
                    if tool_name == "process_f1_to_sheet_and_email":
                        self.context.final_answer = f"FINAL_ANSWER: {result_str}"
                        break

                    query = f"""Original user task: {self.context.user_input}

    Your last tool produced this result:

    {result_str}

    If this fully answers the task, return:
    FINAL_ANSWER: your answer

    Otherwise, return the next FUNCTION_CALL."""
                except Exception as e:
                    print(f"[error] Tool execution failed: {e}")
                    break

        except Exception as e:
            print(f"[agent] Session failed: {e}")

        return self.context.final_answer or "FINAL_ANSWER: [no result]"


