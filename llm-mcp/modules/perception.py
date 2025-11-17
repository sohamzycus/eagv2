from typing import List, Optional
from pydantic import BaseModel
import os
import re
import json
from dotenv import load_dotenv
from modules.model_manager import ModelManager
from modules.tools import summarize_tools

model = ModelManager()
tool_context = summarize_tools(model.get_all_tools()) if hasattr(model, "get_all_tools") else ""


class PerceptionResult(BaseModel):
    user_input: str
    intent: Optional[str] = None
    entities: List[str] = []
    tool_hint: Optional[str] = None


async def extract_perception(user_input: str) -> PerceptionResult:
    """
    Uses LLMs to extract structured info:
    - intent: user’s high-level goal
    - entities: keywords or values
    - tool_hint: likely MCP tool name (optional)
    """

    prompt = f"""
You are an AI that extracts structured facts from user input.

Available tools: {tool_context}

Input: "{user_input}"

Return the response as a Python dictionary with keys:
- intent: (brief phrase about what the user wants)
- entities: a list of strings representing keywords or values (e.g., ["INDIA", "ASCII"])
- tool_hint: (name of the MCP tool that might be useful, if any)
- user_input: same as above

Output only the dictionary on a single line. Do NOT wrap it in ```json or other formatting. Ensure `entities` is a list of strings, not a dictionary.
"""

    try:
        response = await model.generate_text(prompt)

        # Clean up raw if wrapped in markdown-style ```json
        raw = (response or "").strip()
        # Clean and parse
        clean = re.sub(r"^```json|```$", "", raw, flags=re.MULTILINE).strip()
        try:
            parsed = json.loads(clean)
        except Exception as json_error:
            print(f"[perception] JSON parsing failed: {json_error}")
            parsed = {}

        # Heuristic fallback when model didn't return dict
        if not isinstance(parsed, dict) or not parsed:
            hint = None
            lu = user_input.lower()
            if "http" in lu:
                hint = "fetch_content"
            elif "sheet" in lu or "spreadsheet" in lu:
                hint = "create_spreadsheet"
            elif "email" in lu or "mail" in lu:
                hint = "send_email"
            elif "search" in lu or "find" in lu:
                hint = "search_documents"
            return PerceptionResult(user_input=user_input, intent=None, entities=[], tool_hint=hint)

        # Ensure Keys
        if "user_input" not in parsed:
            parsed["user_input"] = user_input
        if "intent" not in parsed:
            parsed['intent'] = None
        # Fix common issues
        if isinstance(parsed.get("entities"), dict):
            parsed["entities"] = list(parsed["entities"].values())

        parsed["user_input"] = user_input  # overwrite or insert safely
        return PerceptionResult(**parsed)

    except Exception as e:
        print(f"[perception] ⚠️ LLM perception failed: {e}")
        # Heuristic minimal fallback
        return PerceptionResult(user_input=user_input, intent=None, entities=[], tool_hint=None)
