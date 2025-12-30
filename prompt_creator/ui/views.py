"""
UI Views for the Prompt Creator.

Provides view components for different aspects of the system.
"""

from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class ConversationMessage:
    """A single message in the conversation."""

    role: str  # "user" or "assistant"
    content: str
    timestamp: str = ""


class ConversationView:
    """
    View component for the conversation interface.

    Manages chat history and formatting.
    """

    def __init__(self):
        self._messages: list[ConversationMessage] = []

    def add_user_message(self, content: str) -> None:
        """Add a user message."""
        self._messages.append(ConversationMessage(role="user", content=content))

    def add_assistant_message(self, content: str) -> None:
        """Add an assistant message."""
        self._messages.append(ConversationMessage(role="assistant", content=content))

    def get_chat_history(self) -> list[tuple[str, str]]:
        """Get chat history in Gradio chatbot format."""
        history = []
        for msg in self._messages:
            if msg.role == "user":
                history.append((msg.content, None))
            else:
                if history and history[-1][1] is None:
                    history[-1] = (history[-1][0], msg.content)
                else:
                    history.append((None, msg.content))
        return history

    def clear(self) -> None:
        """Clear conversation history."""
        self._messages = []

    def get_welcome_message(self) -> str:
        """Get welcome message for new sessions."""
        return """👋 **Welcome to the Prompt Creator!**

I'll help you create a production-ready AI agent prompt for your procurement use case.

**How it works:**
1. Describe your use case in plain language
2. I'll ask a few clarifying questions
3. You'll get a complete system prompt and tool specifications

**Example inputs:**
- "I want an AI that helps employees buy office supplies"
- "Create a procurement bot for IT equipment requests"
- "Build an intake system for service purchases"

**Ready to start?** Just describe what you want your AI assistant to do!"""


class ReasoningView:
    """
    View component for the reasoning timeline.

    Displays agent decision-making process.
    """

    def __init__(self):
        self._reasoning_steps: list[dict[str, Any]] = []

    def add_step(
        self,
        agent: str,
        step: str,
        decision: str,
        next_action: str = None,
    ) -> None:
        """Add a reasoning step."""
        self._reasoning_steps.append({
            "agent": agent,
            "step": step,
            "decision": decision,
            "next": next_action or "—",
        })

    def get_timeline_html(self) -> str:
        """Generate HTML timeline for reasoning steps."""
        if not self._reasoning_steps:
            return "<p><em>No reasoning steps yet. Start a conversation to see the agent's decision-making process.</em></p>"

        html = ['<div class="reasoning-timeline">']

        for i, step in enumerate(self._reasoning_steps):
            agent_color = self._get_agent_color(step["agent"])
            html.append(f'''
                <div class="reasoning-step" style="border-left: 3px solid {agent_color}; padding-left: 10px; margin-bottom: 10px;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span style="font-weight: bold; color: {agent_color};">{step["agent"]}</span>
                        <span style="color: #666; font-size: 0.9em;">{step["step"]}</span>
                    </div>
                    <div style="margin-top: 5px;">{step["decision"]}</div>
                    <div style="color: #888; font-size: 0.85em; margin-top: 3px;">→ {step["next"]}</div>
                </div>
            ''')

        html.append('</div>')
        return "".join(html)

    def get_table_data(self) -> list[list[str]]:
        """Get reasoning data as table rows."""
        return [
            [step["agent"], step["step"], step["decision"], step["next"]]
            for step in self._reasoning_steps
        ]

    def clear(self) -> None:
        """Clear reasoning history."""
        self._reasoning_steps = []

    def _get_agent_color(self, agent: str) -> str:
        """Get color for agent."""
        colors = {
            "intake_orchestrator": "#4CAF50",
            "clarification_agent": "#2196F3",
            "prompt_composer_agent": "#9C27B0",
            "tool_synthesizer_agent": "#FF9800",
        }
        return colors.get(agent, "#607D8B")


class PromptView:
    """
    View component for the generated prompt.

    Displays and formats the system prompt.
    """

    def __init__(self):
        self._prompt: Optional[str] = None

    def set_prompt(self, prompt: str) -> None:
        """Set the generated prompt."""
        self._prompt = prompt

    def get_prompt(self) -> str:
        """Get the generated prompt."""
        return self._prompt or "*No prompt generated yet. Complete the clarification process to see the generated prompt.*"

    def get_prompt_stats(self) -> dict[str, Any]:
        """Get statistics about the prompt."""
        if not self._prompt:
            return {}

        return {
            "characters": len(self._prompt),
            "words": len(self._prompt.split()),
            "lines": len(self._prompt.splitlines()),
            "sections": self._prompt.count("##"),
        }

    def get_preview(self, max_lines: int = 50) -> str:
        """Get a preview of the prompt."""
        if not self._prompt:
            return ""

        lines = self._prompt.splitlines()
        if len(lines) <= max_lines:
            return self._prompt

        preview = "\n".join(lines[:max_lines])
        return f"{preview}\n\n... ({len(lines) - max_lines} more lines)"

    def clear(self) -> None:
        """Clear the prompt."""
        self._prompt = None


class ToolsView:
    """
    View component for generated MCP-Zero tools.

    Displays tool specifications in a user-friendly format.
    """

    def __init__(self):
        self._tools: list[dict[str, Any]] = []

    def set_tools(self, tools: list[dict[str, Any]]) -> None:
        """Set the generated tools."""
        self._tools = tools

    def get_tools_json(self, indent: int = 2) -> str:
        """Get tools as formatted JSON."""
        import json
        if not self._tools:
            return "// No tools generated yet"
        return json.dumps(self._tools, indent=indent)

    def get_tools_summary(self) -> str:
        """Get a summary of generated tools."""
        if not self._tools:
            return "*No tools generated yet.*"

        lines = [f"**{len(self._tools)} Tools Generated**\n"]

        for tool in self._tools:
            tool_name = tool.get("tool_name", "Unknown")
            tool_type = tool.get("type", "internal")
            description = tool.get("description", "No description")

            lines.append(f"### `{tool_name}`")
            lines.append(f"**Type:** {tool_type}")
            lines.append(f"{description}")
            lines.append("")

        return "\n".join(lines)

    def get_tools_table(self) -> list[list[str]]:
        """Get tools as table data."""
        return [
            [
                tool.get("tool_name", ""),
                tool.get("type", ""),
                tool.get("description", "")[:50] + "..." if len(tool.get("description", "")) > 50 else tool.get("description", ""),
            ]
            for tool in self._tools
        ]

    def clear(self) -> None:
        """Clear tools."""
        self._tools = []


class ProgressView:
    """
    View component for showing progress.

    Displays current state and progress bar.
    """

    def __init__(self):
        self._current_step = "init"
        self._total_steps = 5
        self._completed_steps = 0

    def set_progress(self, step: str, completed: int, total: int = 5) -> None:
        """Update progress."""
        self._current_step = step
        self._completed_steps = completed
        self._total_steps = total

    def get_progress_bar(self) -> str:
        """Get progress bar HTML."""
        percentage = int((self._completed_steps / self._total_steps) * 100)
        return f'''
            <div style="margin-bottom: 10px;">
                <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                    <span>Progress</span>
                    <span>{percentage}%</span>
                </div>
                <div style="background: #e0e0e0; border-radius: 5px; height: 10px;">
                    <div style="background: #4CAF50; border-radius: 5px; height: 100%; width: {percentage}%;"></div>
                </div>
                <div style="color: #666; font-size: 0.9em; margin-top: 5px;">
                    Current: {self._current_step}
                </div>
            </div>
        '''

    def get_steps_indicator(self) -> str:
        """Get step indicators."""
        steps = ["Intake", "Clarification", "Intent", "Prompt", "Tools"]
        html = ['<div style="display: flex; justify-content: space-between;">']

        for i, step in enumerate(steps):
            if i < self._completed_steps:
                color = "#4CAF50"
                icon = "✓"
            elif i == self._completed_steps:
                color = "#2196F3"
                icon = "●"
            else:
                color = "#bdbdbd"
                icon = "○"

            html.append(f'''
                <div style="text-align: center;">
                    <div style="color: {color}; font-size: 1.5em;">{icon}</div>
                    <div style="font-size: 0.8em; color: {color};">{step}</div>
                </div>
            ''')

        html.append('</div>')
        return "".join(html)



