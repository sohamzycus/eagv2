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


# System prompt for clarification - business language only
CLARIFICATION_SYSTEM_PROMPT = """You are a Business Requirements Analyst for a procurement system.

Your role is to understand what kind of AI procurement assistant the user wants to create.

RULES:
1. Ask ONLY business-level questions - never technical ones
2. Use simple, clear language that any business user can understand
3. Ask at most 5 questions total
4. Focus on understanding:
   - What employees will purchase (goods, services, or both)
   - How they will purchase (catalog, quotes, direct requests)
   - What approval rules are needed
   - Whether multi-currency support is needed
   - What supplier validation is required

FORBIDDEN:
- Technical terms like "API", "JSON", "schema", "endpoint"
- Implementation details
- Asking about system architecture
- Mentioning steps, workflows, or COVE

When responding to answers, be brief and move to the next question.
When you have enough information, summarize what you understood."""


INTENT_EXTRACTION_PROMPT = """You are a Business Intent Extractor.

Given the conversation about a procurement assistant, extract the requirements as JSON.

Output ONLY valid JSON matching this structure:
{
  "use_case_name": "short name for this use case",
  "supports_goods": true/false,
  "supports_services": true/false,
  "channels": ["catalog", "non_catalog", "quote", "punchout"],
  "quote_upload_enabled": true/false,
  "value_routing_enabled": true/false,
  "supplier_validation_required": true/false,
  "multi_currency": true/false
}

Be conservative - if something wasn't explicitly discussed, use sensible defaults."""


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

        prompt = f"""Based on this conversation about creating a procurement assistant:

{conversation}

What should you ask next to understand the requirements better?
Remember: 
- Only ask 1-2 questions at a time
- Use simple business language
- Focus on what hasn't been clarified yet

If you have enough information to understand the requirements, say so and summarize."""

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
        """Build BusinessIntent from extracted JSON."""
        # Parse channels
        channels = []
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

        return BusinessIntent(
            use_case_name=data.get("use_case_name", "Procurement Assistant"),
            description=original_input,
            supports_goods=data.get("supports_goods", True),
            supports_services=data.get("supports_services", True),
            enabled_channels=channels or [ProcurementChannel.CATALOG],
            quote_upload_enabled=data.get("quote_upload_enabled", False),
            routing_strategy=routing,
            supplier_validation_required=data.get("supplier_validation_required", True),
            compliance_level=ComplianceLevel.STRICT,
            ui_silence_required=True,
            message_prefix_enforcement=True,
            summary_generation=True,
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
            """Thanks for sharing your idea! Let me understand it better.

**A few quick questions:**

1️⃣ Will employees be purchasing **physical goods** (like equipment or supplies), **services** (like consulting), or **both**?

2️⃣ Should they be able to browse a **company catalog**, or will they mainly describe what they need?""",

            """Got it! One more thing:

3️⃣ Do employees need to upload **vendor quotes** for comparison?

4️⃣ Should higher-value purchases require **additional approval** (like from a manager or director)?""",

            """Almost done!

5️⃣ Should the system check if a **supplier is approved** before allowing purchases from them?

That's all I need to know!""",

            """Thanks! I have enough information now.

Let me create your procurement assistant based on what you've told me...""",
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
