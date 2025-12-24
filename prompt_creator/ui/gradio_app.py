"""
Gradio App for the Prompt Creator.

Provides the main UI with conversation, reasoning, and output views.
Uses LIVE LLM execution via Azure OpenAI GPT-4o.
"""

import json
import os
from typing import Any, Optional
from uuid import uuid4

try:
    import gradio as gr
except ImportError:
    gr = None

from prompt_creator.domain.business_intent import BusinessIntent
from prompt_creator.core.agents.agent_factory import AgentFactory, AgentType
from prompt_creator.core.agents.base_agent import AgentContext
from prompt_creator.core.agents.intake_orchestrator import IntakeOrchestrator, OrchestratorState
from prompt_creator.core.agents.clarification_agent import ClarificationAgent
from prompt_creator.core.agents.prompt_composer_agent import PromptComposerAgent
from prompt_creator.core.agents.tool_synthesizer_agent import ToolSynthesizerAgent
from prompt_creator.core.reasoning.reasoning_store import InMemoryReasoningStore
from prompt_creator.core.reasoning.audit_logger import AuditLogger

from .views import ConversationView, ReasoningView, PromptView, ToolsView, ProgressView


class PromptCreatorUI:
    """
    Main UI controller for the Prompt Creator.

    Coordinates between agents and UI views.
    Uses LLM for real execution (not mocks).
    """

    def __init__(self, llm_client=None):
        """
        Initialize UI with optional LLM client.

        Args:
            llm_client: Pre-configured LLM client (or None to try auto-config)
        """
        self._session_id = str(uuid4())
        self._reasoning_store = InMemoryReasoningStore()
        self._audit_logger = AuditLogger()
        self._llm_client = llm_client

        # Try to create LLM client if not provided
        if self._llm_client is None:
            self._llm_client = self._try_create_llm_client()

        # Configure factory with LLM
        AgentFactory.reset()
        self._factory = AgentFactory.configure(
            llm_client=self._llm_client,
            reasoning_store=self._reasoning_store,
        )

        # Initialize agents with LLM injection
        self._orchestrator: IntakeOrchestrator = self._factory.create(
            AgentType.INTAKE_ORCHESTRATOR
        )
        self._clarification: ClarificationAgent = self._factory.create(
            AgentType.CLARIFICATION
        )
        self._composer: PromptComposerAgent = self._factory.create(
            AgentType.PROMPT_COMPOSER
        )
        self._synthesizer: ToolSynthesizerAgent = self._factory.create(
            AgentType.TOOL_SYNTHESIZER
        )

        # Initialize context with LLM
        self._context = AgentContext(
            session_id=self._session_id,
            reasoning_store=self._reasoning_store,
            llm_client=self._llm_client,
        )

        # Initialize views
        self._conversation = ConversationView()
        self._reasoning = ReasoningView()
        self._prompt_view = PromptView()
        self._tools_view = ToolsView()
        self._progress = ProgressView()

        # Start audit session
        self._audit_logger.start_session(self._session_id)

        # Log LLM configuration
        if self._llm_client:
            self._audit_logger.log_agent_action(
                "system",
                "llm_configured",
                input_data={
                    "provider": self._llm_client.provider_name,
                    "model": self._llm_client.model_name,
                },
            )

    def _try_create_llm_client(self):
        """Try to create LLM client from environment."""
        try:
            from prompt_creator.core.llm.llm_factory import LLMFactory
            from prompt_creator.core.llm.llm_config import LLMConfig, LLMProvider

            # Check for Azure OpenAI config
            if os.getenv("AZURE_OPENAI_ENDPOINT") and os.getenv("AZURE_OPENAI_DEPLOYMENT"):
                return LLMFactory.create_azure_gpt4o()

            # Check for OpenAI config
            if os.getenv("OPENAI_API_KEY"):
                return LLMFactory.create_openai_gpt4o()

            # Return mock for demo
            return LLMFactory.create_mock()

        except Exception as e:
            print(f"Warning: Could not create LLM client: {e}")
            return None

    def process_message(self, user_message: str, chat_history: list) -> tuple:
        """
        Process a user message and return updated UI state.

        Uses LIVE LLM execution via the configured client.

        Returns: (chat_history, reasoning_html, prompt_text, tools_json, progress_html)
        """
        if not user_message.strip():
            return (
                chat_history,
                self._reasoning.get_timeline_html(),
                self._prompt_view.get_prompt(),
                self._tools_view.get_tools_json(),
                self._progress.get_progress_bar(),
            )

        # Log user input
        self._audit_logger.log_user_input(user_message)

        # Update context
        self._context = self._context.with_user_input(user_message)
        self._context.add_to_history("user", user_message)

        # Add to chat history
        chat_history = chat_history or []

        # Process through orchestrator
        response = self._orchestrator.execute(self._context)

        # Track reasoning
        self._reasoning.add_step(
            agent=self._orchestrator.name,
            step=self._orchestrator.current_state.name,
            decision=response.reasoning,
            next_action=response.next_agent,
        )

        # Route to appropriate agent
        assistant_message = ""

        if self._orchestrator.current_state == OrchestratorState.CLARIFYING:
            # Run clarification agent (uses LLM)
            clar_response = self._clarification.execute(self._context)

            self._reasoning.add_step(
                agent=self._clarification.name,
                step="CLARIFICATION",
                decision=clar_response.reasoning,
                next_action=clar_response.next_agent,
            )

            if clar_response.requires_user_input:
                assistant_message = clar_response.user_message
            else:
                # Clarification complete, update context
                if hasattr(clar_response.output, "get") and clar_response.output.get("intent"):
                    self._context.intent = clar_response.output["intent"]
                elif isinstance(clar_response.output, dict) and "intent" in clar_response.output:
                    self._context.intent = clar_response.output["intent"]

                assistant_message = clar_response.user_message or "Requirements captured! Generating your prompt..."
                self._orchestrator._state = OrchestratorState.COMPOSING_PROMPT

        if self._orchestrator.current_state == OrchestratorState.COMPOSING_PROMPT:
            if self._context.intent:
                # Run prompt composer (uses LLM)
                comp_response = self._composer.execute(self._context)

                self._reasoning.add_step(
                    agent=self._composer.name,
                    step="PROMPT_COMPOSITION",
                    decision=comp_response.reasoning,
                    next_action=comp_response.next_agent,
                )

                if comp_response.success:
                    self._prompt_view.set_prompt(self._context.generated_prompt)
                    self._orchestrator._state = OrchestratorState.SYNTHESIZING_TOOLS

                    self._audit_logger.log_prompt_generated(
                        len(self._context.generated_prompt),
                    )

        if self._orchestrator.current_state == OrchestratorState.SYNTHESIZING_TOOLS:
            if self._context.intent:
                # Run tool synthesizer (uses LLM)
                synth_response = self._synthesizer.execute(self._context)

                self._reasoning.add_step(
                    agent=self._synthesizer.name,
                    step="TOOL_SYNTHESIS",
                    decision=synth_response.reasoning,
                    next_action="COMPLETE",
                )

                if synth_response.success:
                    self._tools_view.set_tools(self._context.generated_tools)
                    self._orchestrator._state = OrchestratorState.COMPLETE

                    self._audit_logger.log_tools_generated(
                        len(self._context.generated_tools),
                        [t.get("tool_name") for t in self._context.generated_tools],
                    )

                    assistant_message = self._generate_completion_message()

        # Update progress
        self._update_progress()

        # Add to chat (Gradio 6.x messages format)
        if not assistant_message and response.user_message:
            assistant_message = response.user_message

        if user_message:
            chat_history.append({"role": "user", "content": user_message})
        if assistant_message:
            chat_history.append({"role": "assistant", "content": assistant_message})
            self._context.add_to_history("assistant", assistant_message)

        return (
            chat_history,
            self._reasoning.get_timeline_html(),
            self._prompt_view.get_prompt(),
            self._tools_view.get_tools_json(),
            self._progress.get_progress_bar(),
        )

    def _generate_completion_message(self) -> str:
        """Generate completion message with stats."""
        stats = self._prompt_view.get_prompt_stats()
        tool_count = len(self._context.generated_tools or [])

        llm_info = ""
        if self._llm_client:
            llm_info = f"\n**Model:** {self._llm_client.provider_name} / {self._llm_client.model_name}"

        return f"""🎉 **Generation Complete!**

Your procurement assistant is ready!

**Prompt Statistics:**
- {stats.get('characters', 0):,} characters
- {stats.get('lines', 0)} lines
- {stats.get('sections', 0)} sections

**Tools Generated:**
- {tool_count} MCP-Zero tool specifications
{llm_info}

Check the **Generated Prompt** and **Tools** tabs on the right to see the outputs.

Would you like to:
- 📝 Make any modifications?
- 📋 Copy the outputs?
- 🔄 Start over with a new use case?"""

    def _update_progress(self) -> None:
        """Update progress based on orchestrator state."""
        state_to_step = {
            OrchestratorState.INIT: (0, "Starting"),
            OrchestratorState.CLARIFYING: (1, "Clarifying Requirements"),
            OrchestratorState.COMPOSING_PROMPT: (3, "Composing Prompt (LLM)"),
            OrchestratorState.SYNTHESIZING_TOOLS: (4, "Generating Tools (LLM)"),
            OrchestratorState.REVIEW: (5, "Review"),
            OrchestratorState.COMPLETE: (5, "Complete"),
        }

        completed, step_name = state_to_step.get(
            self._orchestrator.current_state,
            (0, "Unknown"),
        )
        self._progress.set_progress(step_name, completed)

    def reset(self) -> tuple:
        """Reset the session."""
        self._audit_logger.end_session("reset")
        self._session_id = str(uuid4())
        AgentFactory.reset()
        self.__init__(llm_client=self._llm_client)

        return (
            [{"role": "assistant", "content": self.get_welcome_message()}],
            self._reasoning.get_timeline_html(),
            self._prompt_view.get_prompt(),
            self._tools_view.get_tools_json(),
            self._progress.get_progress_bar(),
        )

    def get_welcome_message(self) -> str:
        """Get welcome message with LLM status."""
        llm_status = "❌ **No LLM configured** - Running in demo mode"
        if self._llm_client:
            llm_status = f"✅ **LLM Active:** {self._llm_client.provider_name} / {self._llm_client.model_name}"

        return f"""👋 **Welcome to the Prompt Creator!**

{llm_status}

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

    def download_prompt(self) -> str:
        """Get prompt for download."""
        return self._prompt_view.get_prompt()

    def download_tools(self) -> str:
        """Get tools JSON for download."""
        return self._tools_view.get_tools_json()

    def get_llm_stats(self) -> dict:
        """Get LLM usage statistics."""
        if not self._llm_client:
            return {"configured": False}

        return {
            "configured": True,
            "provider": self._llm_client.provider_name,
            "model": self._llm_client.model_name,
        }


def create_app(llm_client=None) -> "gr.Blocks":
    """
    Create the Gradio application.

    Args:
        llm_client: Pre-configured LLM client for live execution

    Returns a Gradio Blocks interface.
    """
    if gr is None:
        raise ImportError("Gradio is not installed. Run: pip install gradio")

    ui = PromptCreatorUI(llm_client=llm_client)
    llm_stats = ui.get_llm_stats()

    llm_badge = "🔴 Demo Mode" if not llm_stats.get("configured") else f"🟢 {llm_stats.get('model', 'LLM')}"

    with gr.Blocks(
        title="Prompt Creator - AI Procurement Assistant Generator",
    ) as app:
        gr.Markdown(f"""
        # 🤖 Prompt Creator
        ### Generate production-ready AI procurement assistant prompts

        **LLM Status:** {llm_badge}

        Describe your use case in plain language, answer a few questions, and get a complete system prompt with MCP-Zero tool specifications.
        """)

        with gr.Row():
            # Left side - Conversation
            with gr.Column(scale=1):
                chatbot = gr.Chatbot(
                    value=[{"role": "assistant", "content": ui.get_welcome_message()}],
                    label="Conversation",
                    height=500,
                )

                with gr.Row():
                    msg_input = gr.Textbox(
                        placeholder="Describe your procurement use case...",
                        label="Your Message",
                        lines=2,
                        scale=4,
                    )
                    send_btn = gr.Button("Send", variant="primary", scale=1)

                with gr.Row():
                    reset_btn = gr.Button("🔄 New Session", variant="secondary")

            # Right side - Outputs (Tabbed)
            with gr.Column(scale=1):
                with gr.Tabs():
                    with gr.Tab("🧠 Reasoning"):
                        reasoning_html = gr.HTML(
                            value="<p><em>Start a conversation to see the agent's decision-making process.</em></p>",
                            label="Agent Reasoning Timeline",
                        )

                    with gr.Tab("📄 Generated Prompt"):
                        prompt_output = gr.Markdown(
                            value="*Complete the clarification process to see the generated prompt.*",
                            label="System Prompt",
                        )
                        download_prompt_btn = gr.Button("📥 Download Prompt")

                    with gr.Tab("🛠️ Tools (MCP-Zero)"):
                        tools_output = gr.Code(
                            value="// No tools generated yet",
                            language="json",
                            label="MCP-Zero Tool Specifications",
                        )
                        download_tools_btn = gr.Button("📥 Download Tools JSON")

                    with gr.Tab("📊 Progress"):
                        progress_html = gr.HTML(
                            value=ui._progress.get_progress_bar(),
                            label="Generation Progress",
                        )

        # Example inputs
        gr.Examples(
            examples=[
                ["I want an AI that helps employees buy office supplies and equipment"],
                ["Create a procurement bot for IT hardware requests with quote support"],
                ["Build an intake system for service purchases that routes based on value"],
                ["I need a bot to help employees submit purchase requests for both goods and services"],
            ],
            inputs=msg_input,
            label="Example Use Cases",
        )

        # Event handlers
        def on_send(message, history):
            return ui.process_message(message, history)

        send_btn.click(
            fn=on_send,
            inputs=[msg_input, chatbot],
            outputs=[chatbot, reasoning_html, prompt_output, tools_output, progress_html],
        ).then(
            fn=lambda: "",
            outputs=msg_input,
        )

        msg_input.submit(
            fn=on_send,
            inputs=[msg_input, chatbot],
            outputs=[chatbot, reasoning_html, prompt_output, tools_output, progress_html],
        ).then(
            fn=lambda: "",
            outputs=msg_input,
        )

        reset_btn.click(
            fn=ui.reset,
            outputs=[chatbot, reasoning_html, prompt_output, tools_output, progress_html],
        )

    return app


if __name__ == "__main__":
    app = create_app()
    app.launch()
