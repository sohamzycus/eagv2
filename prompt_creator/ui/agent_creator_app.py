"""
Agent Creator App - LLM-Driven Conversational Experience

Uses GPT-4o to drive intelligent, contextual conversations for creating procurement agents.
NO hardcoded responses - everything is LLM-generated.
"""

import gradio as gr
import json
import os
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from uuid import uuid4


# System prompt for the Agent Creator AI
AGENT_CREATOR_SYSTEM_PROMPT = """You are an expert AI Agent Designer specializing in enterprise procurement workflows.

Your role is to help users create production-ready AI agents for ANY procurement workflow:
- Buy/Purchase flows
- Invoice processing (AP)
- Sourcing (RFx)
- Contract management
- Supplier management
- Goods receipt
- Custom workflows

## Your Approach

1. **Understand Intent First**: Ask clarifying questions to understand exactly what the user wants
2. **Be Conversational**: Respond naturally, not with rigid templates
3. **Show Options**: Present numbered choices [1], [2], [3] when appropriate
4. **Visualize Workflows**: Use simple text-based workflow diagrams
5. **Identify Tools**: Suggest what tools/APIs the agent will need
6. **Generate Output**: Create complete system prompts when ready

## Conversation Flow

1. **Welcome & Intent**: Understand what type of agent they want
2. **Experience Level**: Ask how autonomous vs guided the agent should be
3. **Workflow Design**: Collaboratively design the workflow stages
4. **Refinement**: Let user modify/add stages based on their input
5. **Tool Identification**: Identify required tools for each stage
6. **Generation**: Generate the complete system prompt

## Important Rules

- NEVER assume - always ask if unclear
- Use business language, not technical jargon
- When user provides feedback, INCORPORATE it intelligently
- Show workflow as simple numbered steps, NOT mermaid diagrams
- Be helpful and guide them through the process
- When generating the final prompt, make it COMPLETE and production-ready

## Response Format

- Use markdown for formatting
- Use **bold** for emphasis
- Use numbered lists [1], [2], [3] for options
- Use bullet points for details
- Show workflows as numbered steps with arrows (→)

## Example Workflow Display

```
📋 Workflow Stages:

1️⃣ Intent Capture
   → Understand what user wants to buy
   
2️⃣ Smart Item Discovery  
   → Search catalog, past POs, punchouts
   
3️⃣ Item Selection
   → User reviews and decides
   
4️⃣ Purchase Execution
   → Create requisition/PO
```

Start by warmly greeting the user and asking what kind of procurement agent they want to create."""


@dataclass
class ConversationState:
    """Tracks conversation state."""
    session_id: str = ""
    workflow_type: str = ""
    workflow_stages: List[str] = field(default_factory=list)
    tools: List[Dict] = field(default_factory=list)
    experience_level: str = ""
    ready_to_generate: bool = False
    generated_prompt: str = ""


class AgentCreatorApp:
    """LLM-driven agent creator."""
    
    def __init__(self, llm_client=None):
        self.llm = llm_client
        self.state = ConversationState(session_id=str(uuid4()))
        self.conversation_history: List[Dict[str, str]] = []
    
    def get_welcome_message(self) -> str:
        """Get the initial welcome message from LLM."""
        if self.llm:
            try:
                response = self.llm.generate_simple(
                    system_prompt=AGENT_CREATOR_SYSTEM_PROMPT,
                    user_message="Start a new session. Greet the user warmly and ask what kind of procurement agent they want to create. Be concise but friendly.",
                    temperature=0.7
                )
                return response
            except Exception as e:
                print(f"LLM error: {e}")
        
        # Fallback if no LLM
        return """# 🤖 Procurement Agent Creator

Welcome! I'm here to help you design an AI agent for your procurement workflows.

**What can I help you build?**
- 🛒 Purchase/Buy assistants
- 📄 Invoice processing agents
- 🔍 Sourcing assistants
- 📝 Contract management
- 👥 Supplier management
- 📦 Goods receipt workflows
- Or something custom!

**What kind of procurement agent would you like to create?**

*Just describe what you need in your own words, and I'll help you design it step by step.*"""

    def process_message(self, user_message: str, history: List) -> tuple:
        """Process user message using LLM."""
        if not user_message.strip():
            return history, self._get_status_display()
        
        # Add user message to history
        history = history or []
        history.append({"role": "user", "content": user_message})
        self.conversation_history.append({"role": "user", "content": user_message})
        
        # Generate response using LLM
        response = self._generate_response(user_message)
        
        # Add assistant response
        history.append({"role": "assistant", "content": response})
        self.conversation_history.append({"role": "assistant", "content": response})
        
        # Update state based on conversation
        self._update_state_from_conversation(user_message, response)
        
        return history, self._get_status_display()
    
    def _generate_response(self, user_message: str) -> str:
        """Generate response using LLM."""
        if not self.llm:
            return self._generate_fallback_response(user_message)
        
        try:
            # Build context from conversation history
            context = self._build_conversation_context()
            
            # Add current state info
            state_info = f"""
Current session state:
- Workflow type: {self.state.workflow_type or 'Not determined'}
- Stages defined: {len(self.state.workflow_stages)}
- Experience level: {self.state.experience_level or 'Not set'}
- Ready to generate: {self.state.ready_to_generate}
"""
            
            full_prompt = f"""{context}

{state_info}

User's latest message: {user_message}

Respond helpfully. If they're providing feedback or modifications to the workflow, incorporate them.
If they seem ready, ask if they want to generate the final prompt.
If they say "generate", "yes", "create", or similar - generate a COMPLETE system prompt for their agent."""

            response = self.llm.generate_simple(
                system_prompt=AGENT_CREATOR_SYSTEM_PROMPT,
                user_message=full_prompt,
                temperature=0.5
            )
            
            return response
            
        except Exception as e:
            print(f"LLM error: {e}")
            return self._generate_fallback_response(user_message)
    
    def _build_conversation_context(self) -> str:
        """Build context from conversation history."""
        if not self.conversation_history:
            return "This is the start of a new conversation."
        
        # Get last 10 messages for context
        recent = self.conversation_history[-10:]
        context_lines = []
        
        for msg in recent:
            role = "User" if msg["role"] == "user" else "Assistant"
            content = msg["content"][:500]  # Truncate long messages
            context_lines.append(f"{role}: {content}")
        
        return "Conversation so far:\n" + "\n".join(context_lines)
    
    def _update_state_from_conversation(self, user_message: str, response: str) -> None:
        """Update state based on conversation content."""
        lower_msg = user_message.lower()
        lower_resp = response.lower()
        
        # Detect workflow type
        if not self.state.workflow_type:
            type_keywords = {
                "buy": ["buy", "purchase", "procurement", "requisition"],
                "invoice": ["invoice", "ap ", "accounts payable", "payment"],
                "sourcing": ["sourcing", "rfp", "rfq", "rfi", "bid"],
                "contract": ["contract", "agreement", "renewal"],
                "supplier": ["supplier", "vendor", "onboard"],
                "receiving": ["goods receipt", "grn", "receiving", "delivery"],
            }
            for wtype, keywords in type_keywords.items():
                if any(kw in lower_msg for kw in keywords):
                    self.state.workflow_type = wtype
                    break
        
        # Detect experience level
        if not self.state.experience_level:
            if any(x in lower_msg for x in ["guided", "1", "confirm", "checkpoint"]):
                self.state.experience_level = "guided"
            elif any(x in lower_msg for x in ["autonomous", "3", "independent"]):
                self.state.experience_level = "autonomous"
            elif any(x in lower_msg for x in ["balanced", "2"]):
                self.state.experience_level = "balanced"
        
        # Detect if ready to generate
        if any(x in lower_msg for x in ["generate", "create", "build", "yes, generate"]):
            if "workflow" in lower_resp or "stages" in lower_resp:
                self.state.ready_to_generate = True
        
        # Check if response contains generated prompt
        if "# system prompt" in lower_resp or "## system identity" in lower_resp:
            self.state.generated_prompt = response
    
    def _generate_fallback_response(self, user_message: str) -> str:
        """Fallback when LLM is not available."""
        lower = user_message.lower()
        
        if any(x in lower for x in ["buy", "purchase", "procurement"]):
            return """Great! You want to create a **Buy/Purchase Assistant**.

Let me understand your requirements:

**[1]** What sources should the agent search for items?
- Catalog
- Past purchase orders
- External catalogs (Punchouts)
- All of the above

**[2]** What happens if the item isn't found in any source?
- Create a custom request
- Escalate to a buyer
- Both options

Please share your preferences, or describe your ideal workflow!"""
        
        elif any(x in lower for x in ["invoice", "ap", "payment"]):
            return """I'll help you create an **Invoice Processing Assistant**.

To design the right workflow:

**[1]** What type of matching do you need?
- 2-way (Invoice ↔ PO)
- 3-way (Invoice ↔ PO ↔ GRN)

**[2]** How should exceptions be handled?
- Auto-route to AP team
- Flag for manual review
- Both based on exception type

Tell me more about your invoice processing needs!"""
        
        else:
            return """I'd love to help you create that agent!

Could you tell me more about:
1. **Who** will use this agent? (employees, managers, AP team, etc.)
2. **What** is the main task they need to accomplish?
3. **What systems** should it connect to?

Feel free to describe your ideal workflow, and I'll help you structure it!"""
    
    def _get_status_display(self) -> str:
        """Get current status for sidebar."""
        status_icon = lambda x: "✅" if x else "⏳"
        
        return f"""## 📊 Session Status

**Workflow Type:** {self.state.workflow_type or '*Identifying...*'}
**Experience Level:** {self.state.experience_level or '*Not set*'}
**Stages Defined:** {len(self.state.workflow_stages) or '*In progress*'}

---

### Progress

{status_icon(self.state.workflow_type)} Workflow Type
{status_icon(self.state.experience_level)} Experience Level  
{status_icon(len(self.state.workflow_stages) > 0)} Workflow Design
{status_icon(len(self.state.tools) > 0)} Tool Identification
{status_icon(self.state.generated_prompt)} Prompt Generated

---

*The AI will guide you through each step. Just describe what you need!*"""
    
    def reset(self) -> tuple:
        """Reset the session."""
        self.state = ConversationState(session_id=str(uuid4()))
        self.conversation_history = []
        
        welcome = self.get_welcome_message()
        return (
            [{"role": "assistant", "content": welcome}],
            self._get_status_display()
        )


def create_agent_creator_app(llm_client=None):
    """Create the Gradio app."""
    creator = AgentCreatorApp(llm_client=llm_client)
    
    # Check LLM status
    llm_status = "🟢 GPT-4o Connected" if llm_client else "🔴 Demo Mode (No LLM)"
    
    with gr.Blocks(
        title="Procurement Agent Creator",
    ) as app:
        gr.Markdown(f"""
# 🤖 Procurement Agent Creator
### Design AI agents for any procurement workflow using natural conversation

**Status:** {llm_status}
        """)
        
        with gr.Row():
            with gr.Column(scale=3):
                chatbot = gr.Chatbot(
                    value=[{"role": "assistant", "content": creator.get_welcome_message()}],
                    height=550,
                    label="Conversation",
                )
                
                with gr.Row():
                    msg_input = gr.Textbox(
                        placeholder="Describe what you want to build...",
                        label="Your Message",
                        lines=2,
                        scale=4,
                    )
                    send_btn = gr.Button("Send", variant="primary", scale=1)
                
                with gr.Row():
                    reset_btn = gr.Button("🔄 Start New Session", variant="secondary")
            
            with gr.Column(scale=1):
                status_display = gr.Markdown(
                    value=creator._get_status_display(),
                    label="Status",
                )
        
        # Examples
        gr.Markdown("### 💡 Example Prompts")
        gr.Examples(
            examples=[
                ["I want to create an agent that helps employees buy items"],
                ["Build an invoice processing assistant with 3-way matching"],
                ["Create a sourcing agent for RFP management"],
                ["I need a supplier onboarding workflow assistant"],
            ],
            inputs=msg_input,
        )
        
        # Event handlers
        def on_send(message, history):
            new_history, status = creator.process_message(message, history)
            return new_history, status, ""
        
        send_btn.click(
            fn=on_send,
            inputs=[msg_input, chatbot],
            outputs=[chatbot, status_display, msg_input],
        )
        
        msg_input.submit(
            fn=on_send,
            inputs=[msg_input, chatbot],
            outputs=[chatbot, status_display, msg_input],
        )
        
        reset_btn.click(
            fn=creator.reset,
            outputs=[chatbot, status_display],
        )
    
    return app


# Entry point
if __name__ == "__main__":
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    # Try to load LLM client
    llm_client = None
    try:
        from dotenv import load_dotenv
        load_dotenv()
        
        api_key = os.getenv("AZURE_OPENAI_API_KEY")
        if api_key:
            from core.llm.llm_factory import LLMFactory
            llm_client = LLMFactory.create_zycus_gpt4o(api_key=api_key)
            print("✅ Connected to Azure OpenAI GPT-4o")
    except Exception as e:
        print(f"⚠️ Could not connect to LLM: {e}")
        print("Running in demo mode")
    
    app = create_agent_creator_app(llm_client=llm_client)
    app.launch(server_port=7863, server_name="0.0.0.0")

