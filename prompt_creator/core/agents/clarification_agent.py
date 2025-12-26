"""
Clarification Agent.

Converts vague business input into structured intent.
Uses LLM for intelligent question generation and response parsing.
"""

import json
import re
from typing import Any, Optional, TYPE_CHECKING

from prompt_creator.domain.business_intent import (
    BusinessIntent,
    ComplianceLevel,
    CurrencyConfig,
    ProcurementChannel,
    RoutingStrategy,
    ValueThreshold,
)
from prompt_creator.domain.clarification_model import (
    ClarificationQuestion,
    ClarificationSession,
    QuestionType,
    StandardQuestions,
    UserResponse,
)

from .base_agent import (
    Agent,
    AgentCapability,
    AgentContext,
    AgentResponse,
    LLMEnabledAgent,
    ReasoningStore,
)

if TYPE_CHECKING:
    from prompt_creator.core.llm.llm_client import LLMClient


# System prompt for clarification - PROCUREMENT DOMAIN SPECIALIST
CLARIFICATION_SYSTEM_PROMPT = """You are a Procurement Domain Expert helping users define AI assistant requirements.

Your role is to understand what kind of PROCUREMENT workflow assistant the user needs. The procurement domain includes:

**Source-to-Pay (S2P) Workflows:**
- Sourcing & RFx (RFP, RFQ, RFI)
- Supplier Discovery & Qualification
- Contract Management & Negotiation
- Catalog Management

**Procure-to-Pay (P2P) Workflows:**
- Purchase Requisition (PR) Creation
- Purchase Order (PO) Management
- Goods Receipt & Services Entry
- Invoice Processing & Matching (2-way, 3-way)
- Payment Processing

**Supplier Management:**
- Supplier Onboarding
- Supplier Performance Management
- Supplier Risk Assessment

**Spend Management:**
- Spend Analysis
- Budget Tracking
- Approval Workflows

CRITICAL RULES:
1. Identify WHICH procurement workflow they need (Invoice? PR? PO? Sourcing? Contract?)
2. Ask questions SPECIFIC to that workflow
3. Use procurement terminology they understand
4. Ask at most 3-4 focused questions
5. Understand integrations needed (ERP, AP system, email)

WHAT TO CLARIFY FOR EACH WORKFLOW:

For INVOICE workflows:
- Invoice types (PO-based, non-PO, credit notes)
- Matching requirements (2-way, 3-way)
- Exception handling
- Approval thresholds
- ERP integration

For PURCHASE REQUISITION workflows:
- Goods vs Services
- Catalog vs Non-catalog
- Approval hierarchy
- Budget checks

For SOURCING workflows:
- RFx types needed
- Supplier evaluation criteria
- Award process

For CONTRACT workflows:
- Contract types
- Renewal tracking
- Compliance requirements

FORBIDDEN:
- Technical terms like "API", "JSON", "schema", "endpoint"
- Asking about unrelated workflows
- Mentioning steps, COVE, or internal logic

When responding, be brief and ask RELEVANT questions about THEIR specific procurement workflow.
When you have enough information, summarize what you understood."""


INTENT_EXTRACTION_PROMPT = """You are a Procurement Domain Intent Extractor.

Given the conversation about a procurement workflow assistant, extract the requirements as JSON.

FIRST identify the WORKFLOW TYPE from these categories:
- INVOICE: Invoice processing, AP, 2-way/3-way matching, payment
- REQUISITION: Purchase requisition (PR), buying, purchase requests
- PO: Purchase order management
- SOURCING: RFP, RFQ, RFI, supplier discovery
- CONTRACT: Contract management, renewals
- SUPPLIER: Supplier management, onboarding, performance
- RECEIVING: Goods receipt, GRN, delivery
- SPEND: Spend analysis, budget tracking

Output ONLY valid JSON:
{
  "use_case_name": "descriptive name (e.g., 'Invoice Processing Assistant')",
  "workflow_type": "INVOICE|REQUISITION|PO|SOURCING|CONTRACT|SUPPLIER|RECEIVING|SPEND",
  "description": "detailed description of the workflow",
  "primary_users": "who will use this",
  "key_workflows": ["specific workflow steps mentioned"],
  "validations_needed": ["specific validations required"],
  "approvals_needed": true/false,
  "value_routing_enabled": true/false,
  "integrations_suggested": ["ERP", "AP System", "etc."],
  "compliance_level": "strict/moderate/flexible",
  "supports_goods": true/false,
  "supports_services": true/false,
  "channels": ["catalog", "non_catalog", "quote"],
  "quote_upload_enabled": true/false,
  "supplier_validation_required": true/false,
  "matching_type": "none|2-way|3-way" (for invoice workflows)
}

Be specific about the workflow type based on the conversation."""


class ClarificationAgent(LLMEnabledAgent):
    """
    Agent responsible for gathering business requirements.

    Uses LLM for:
    - Generating clarifying questions
    - Parsing user responses
    - Extracting structured intent
    """

    def __init__(
        self,
        llm_client: Optional["LLMClient"] = None,
        reasoning_store: Optional[ReasoningStore] = None,
    ):
        super().__init__(
            name="clarification_agent",
            capabilities=[AgentCapability.CLARIFICATION],
            llm_client=llm_client,
            reasoning_store=reasoning_store,
        )
        self._sessions: dict[str, ClarificationSession] = {}
        self._conversation_history: dict[str, list[dict]] = {}
        self.set_system_prompt(CLARIFICATION_SYSTEM_PROMPT)

    def can_handle(self, context: AgentContext) -> bool:
        """Can handle if intent is not yet complete."""
        return context.intent is None

    def execute(self, context: AgentContext) -> AgentResponse:
        """
        Execute clarification using LLM.

        Returns either a question to ask or a completed intent.
        """
        session_id = context.session_id

        # Initialize conversation history
        if session_id not in self._conversation_history:
            self._conversation_history[session_id] = []

        history = self._conversation_history[session_id]

        # Check if this is the first message
        is_first_message = len(history) == 0

        if is_first_message:
            # First message - generate initial clarifying questions
            return self._handle_first_message(context, history)
        else:
            # Subsequent message - process response and maybe ask more
            return self._handle_followup(context, history)

    def _handle_first_message(
        self, context: AgentContext, history: list
    ) -> AgentResponse:
        """Handle the first message from user."""
        user_input = context.user_input

        # Add to history
        history.append({"role": "user", "content": user_input})

        # Check if we can use LLM
        if self.has_llm() or context.llm_client:
            # Use LLM to generate intelligent questions
            response = self._ask_llm_for_clarification(user_input, history, context)
        else:
            # Fallback to rule-based questions
            response = self._get_fallback_question(0)

        history.append({"role": "assistant", "content": response})

        context.log_reasoning(
            agent_name=self.name,
            step="INITIAL_CLARIFICATION",
            input_data={"user_input": user_input},
            decision="Asked clarifying questions",
            output={"response": response[:100] + "..."},
            next_step="AWAIT_RESPONSE",
        )

        return AgentResponse.needs_input_response(
            message=response,
            reasoning="Generated clarifying questions based on initial input",
        )

    def _handle_followup(
        self, context: AgentContext, history: list
    ) -> AgentResponse:
        """Handle follow-up messages."""
        user_input = context.user_input
        history.append({"role": "user", "content": user_input})

        # Count exchanges (user messages)
        user_messages = [h for h in history if h["role"] == "user"]

        # After 3-4 exchanges, try to extract intent
        if len(user_messages) >= 3:
            intent = self._extract_intent(history, context)

            if intent:
                context.intent = intent
                summary = self._generate_summary(intent)

                context.log_reasoning(
                    agent_name=self.name,
                    step="INTENT_EXTRACTED",
                    input_data={"conversation_length": len(history)},
                    decision="Intent successfully extracted",
                    output={"intent": intent.use_case_name},
                    next_step="prompt_composer_agent",
                )

                return AgentResponse.success_response(
                    output={"intent": intent},
                    reasoning="Clarification complete - intent captured from conversation",
                    next_agent="intake_orchestrator",
                    user_message=summary,
                )

        # Continue asking questions
        if self.has_llm() or context.llm_client:
            response = self._ask_llm_for_clarification(
                user_input, history, context
            )
        else:
            question_index = len(user_messages)
            response = self._get_fallback_question(question_index)

        history.append({"role": "assistant", "content": response})

        # Check if we've reached max questions
        if len(user_messages) >= 5:
            # Force extraction
            intent = self._extract_intent(history, context)
            if intent:
                context.intent = intent
                return AgentResponse.success_response(
                    output={"intent": intent},
                    reasoning="Max questions reached - extracted intent",
                    next_agent="intake_orchestrator",
                    user_message=self._generate_summary(intent),
                )

        return AgentResponse.needs_input_response(
            message=response,
            reasoning=f"Continuing clarification (question {len(user_messages)})",
        )

    def _ask_llm_for_clarification(
        self,
        user_input: str,
        history: list,
        context: AgentContext,
    ) -> str:
        """Use LLM to generate clarifying questions."""
        # Build conversation for LLM
        conversation = "\n".join([
            f"{'User' if h['role'] == 'user' else 'Assistant'}: {h['content']}"
            for h in history
        ])

        # Get the original request to understand the domain
        original_request = history[0]["content"] if history else user_input

        prompt = f"""The user wants to create an AI assistant. Their original request was:
"{original_request}"

Here's the conversation so far:
{conversation}

CRITICAL: Ask questions that are RELEVANT to what the user asked for!
- If they asked about "invoice flow" - ask about invoices, approval, validation
- If they asked about "procurement" - ask about purchasing, catalogs, suppliers
- If they asked about "HR" - ask about employees, onboarding, policies
- DO NOT ask generic procurement questions if they asked about something else!

What should you ask next to understand their specific requirements?
- Ask 1-2 focused questions
- Use simple business language
- Stay on topic with THEIR domain

If you have enough information, say so and summarize what you understood."""

        try:
            llm = self._llm or context.llm_client
            if llm:
                response = llm.generate_simple(
                    system_prompt=self._system_prompt,
                    user_message=prompt,
                    temperature=0.3,
                )
                return response
        except Exception as e:
            # Log error but continue with fallback
            print(f"LLM clarification error: {e}")
            pass

        # Fallback
        return self._get_fallback_question(len([h for h in history if h["role"] == "user"]))

    def _extract_intent(
        self,
        history: list,
        context: AgentContext,
    ) -> Optional[BusinessIntent]:
        """Extract BusinessIntent from conversation using LLM."""
        conversation = "\n".join([
            f"{'User' if h['role'] == 'user' else 'Assistant'}: {h['content']}"
            for h in history
        ])

        try:
            llm = self._llm or context.llm_client
            if llm:
                response = llm.generate_simple(
                    system_prompt=INTENT_EXTRACTION_PROMPT,
                    user_message=f"Extract requirements from:\n\n{conversation}",
                    temperature=0.0,
                )

                # Parse JSON from response
                intent_data = self._parse_json_response(response)
                if intent_data:
                    return self._build_intent_from_json(intent_data, history[0]["content"])

        except Exception as e:
            pass

        # Fallback to rule-based extraction
        return self._build_intent_from_conversation(history, context)

    def _parse_json_response(self, response: str) -> Optional[dict]:
        """Parse JSON from LLM response."""
        # Try direct parse
        try:
            return json.loads(response)
        except:
            pass

        # Try to extract JSON from markdown code block
        json_match = re.search(r"```(?:json)?\s*({.*?})\s*```", response, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except:
                pass

        # Try to find JSON object in text
        json_match = re.search(r"({[^{}]*(?:{[^{}]*}[^{}]*)*})", response, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except:
                pass

        return None

    def _build_intent_from_json(
        self,
        data: dict,
        original_input: str,
    ) -> BusinessIntent:
        """Build BusinessIntent from extracted JSON - handles any domain."""
        # Determine domain from extracted data
        domain = data.get("domain", "general").lower()
        
        # For procurement-specific use cases, parse channels
        channels = []
        if domain in ["procurement", "purchasing", "buy"]:
            channel_map = {
                "catalog": ProcurementChannel.CATALOG,
                "non_catalog": ProcurementChannel.NON_CATALOG,
                "quote": ProcurementChannel.QUOTE,
                "punchout": ProcurementChannel.PUNCHOUT,
                "contract": ProcurementChannel.CONTRACT,
            }

            for ch in data.get("channels", ["catalog", "non_catalog"]):
                if ch.lower() in channel_map:
                    channels.append(channel_map[ch.lower()])

            routing = (
                RoutingStrategy.THRESHOLD_BASED
                if data.get("value_routing_enabled", True)
                else RoutingStrategy.NONE
            )
            
            supports_goods = data.get("supports_goods", True)
            supports_services = data.get("supports_services", True)
            quote_enabled = data.get("quote_upload_enabled", False)
            supplier_validation = data.get("supplier_validation_required", True)
        else:
            # For non-procurement domains (invoice, hr, support, etc.)
            # Use sensible defaults
            channels = [ProcurementChannel.NON_CATALOG]  # Generic workflow
            routing = (
                RoutingStrategy.THRESHOLD_BASED
                if data.get("approvals_needed", True)
                else RoutingStrategy.NONE
            )
            supports_goods = False
            supports_services = True  # Most workflows are service-like
            quote_enabled = False
            supplier_validation = False

        # Parse compliance level
        compliance_str = data.get("compliance_level", "strict").lower()
        compliance_map = {
            "strict": ComplianceLevel.STRICT,
            "moderate": ComplianceLevel.STANDARD,
            "standard": ComplianceLevel.STANDARD,
            "flexible": ComplianceLevel.RELAXED,
            "relaxed": ComplianceLevel.RELAXED,
        }
        compliance = compliance_map.get(compliance_str, ComplianceLevel.STRICT)

        # Build description from extracted data
        description = data.get("description", original_input)
        
        # Store additional domain-specific data in custom_guardrails and custom_steps
        custom_guardrails = []
        custom_steps = []
        
        if data.get("key_workflows"):
            custom_steps.extend(data['key_workflows'])
        if data.get("validations_needed"):
            for validation in data['validations_needed']:
                custom_guardrails.append(f"ALWAYS validate: {validation}")
        if data.get("integrations_suggested"):
            for integration in data['integrations_suggested']:
                custom_steps.append(f"Integration with {integration}")
        if data.get("primary_users"):
            custom_guardrails.append(f"Primary users: {data['primary_users']}")

        return BusinessIntent(
            use_case_name=data.get("use_case_name", f"{domain.title()} Assistant"),
            description=description,
            supports_goods=supports_goods,
            supports_services=supports_services,
            enabled_channels=channels or [ProcurementChannel.NON_CATALOG],
            quote_upload_enabled=quote_enabled,
            routing_strategy=routing,
            supplier_validation_required=supplier_validation,
            compliance_level=compliance,
            ui_silence_required=True,
            message_prefix_enforcement=True,
            summary_generation=True,
            custom_guardrails=custom_guardrails,
            custom_steps=custom_steps,
        )

    def _build_intent_from_conversation(
        self,
        history: list,
        context: AgentContext,
    ) -> BusinessIntent:
        """Fallback: Build intent from conversation using rules."""
        full_text = " ".join(h["content"] for h in history).lower()

        # Simple pattern matching
        supports_goods = any(
            term in full_text
            for term in ["goods", "products", "equipment", "supplies", "items"]
        )
        supports_services = any(
            term in full_text
            for term in ["services", "consulting", "professional", "work"]
        )

        if not supports_goods and not supports_services:
            supports_goods = supports_services = True

        channels = [ProcurementChannel.CATALOG]
        if "non-catalog" in full_text or "non catalog" in full_text:
            channels.append(ProcurementChannel.NON_CATALOG)
        if "quote" in full_text:
            channels.append(ProcurementChannel.QUOTE)

        quote_enabled = "quote" in full_text
        value_routing = any(
            term in full_text
            for term in ["approval", "route", "routing", "threshold", "value"]
        )

        return BusinessIntent(
            use_case_name=self._extract_use_case_name(history[0]["content"]),
            description=history[0]["content"],
            supports_goods=supports_goods,
            supports_services=supports_services,
            enabled_channels=channels,
            quote_upload_enabled=quote_enabled,
            routing_strategy=RoutingStrategy.THRESHOLD_BASED if value_routing else RoutingStrategy.NONE,
            supplier_validation_required=True,
            compliance_level=ComplianceLevel.STRICT,
            ui_silence_required=True,
            message_prefix_enforcement=True,
            summary_generation=True,
        )

    def _extract_use_case_name(self, user_input: str) -> str:
        """Extract a concise use case name from user input."""
        words = user_input.split()
        if len(words) <= 5:
            return user_input.strip()

        keywords = ["purchase", "buy", "procurement", "request", "intake", "order"]
        for i, word in enumerate(words):
            if word.lower() in keywords:
                start = max(0, i - 2)
                end = min(len(words), i + 3)
                return " ".join(words[start:end]).strip()

        return " ".join(words[:5]).strip()

    def _get_fallback_question(self, index: int) -> str:
        """Get fallback question when LLM is not available."""
        questions = [
            """Thank you for sharing! To clarify the requirements further:

1. **Who will use this assistant?** (e.g., employees, managers, customers, vendors)

2. **What are the main tasks or workflows it should handle?**

Let me know so I can better understand your needs!""",

            """Got it! A couple more questions:

3. **What validations or checks should the system perform?**

4. **Are there any approval workflows needed?** (e.g., manager approval for certain actions)""",

            """Almost there!

5. **What other systems might this need to connect with?** (e.g., ERP, email, document storage)

That's all I need!""",

            """Thanks! I have enough information now.

Let me create your AI assistant based on what you've told me...""",
        ]

        return questions[min(index, len(questions) - 1)]

    def _generate_summary(self, intent: BusinessIntent) -> str:
        """Generate a summary of the captured intent."""
        lines = [
            "✅ **Requirements Captured**",
            "",
            f"**Use Case:** {intent.use_case_name}",
            "",
            "**Configuration:**",
            f"- Procurement: {'Goods & Services' if intent.supports_goods and intent.supports_services else 'Goods' if intent.supports_goods else 'Services'}",
            f"- Channels: {', '.join(intent.get_enabled_channel_names())}",
            f"- Quote Support: {'Yes' if intent.quote_upload_enabled else 'No'}",
            f"- Value Routing: {'Yes' if intent.requires_value_routing() else 'No'}",
            f"- Supplier Validation: {'Yes' if intent.supplier_validation_required else 'No'}",
            "",
            "🔧 **Generating your system prompt now...**",
        ]
        return "\n".join(lines)
