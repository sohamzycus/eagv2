"""
Enhanced Gradio App - LibreChat-style Experience

A professional, step-by-step workflow creation experience for procurement AI agents.
"""

import gradio as gr
import json
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional, List, Dict, Any
from uuid import uuid4


class WorkflowStep(Enum):
    """Workflow creation steps."""
    WELCOME = auto()
    WORKFLOW_TYPE = auto()
    EXPERIENCE_LEVEL = auto()
    HIGH_LEVEL_WORKFLOW = auto()
    WORKFLOW_CONFIRMATION = auto()
    DETAIL_GATHERING = auto()
    TOOL_IDENTIFICATION = auto()
    BUNDLE_NAMING = auto()
    HLD_GENERATION = auto()
    FINAL_REVIEW = auto()
    GENERATION = auto()
    COMPLETE = auto()


@dataclass
class WorkflowState:
    """State management for workflow creation."""
    step: WorkflowStep = WorkflowStep.WELCOME
    workflow_type: str = ""
    workflow_name: str = ""
    experience_level: str = "balanced"
    description: str = ""
    target_users: str = ""
    workflow_stages: List[str] = field(default_factory=list)
    tools_identified: List[Dict] = field(default_factory=list)
    custom_requirements: List[str] = field(default_factory=list)
    bundle_name: str = ""
    conversation_history: List[Dict] = field(default_factory=list)
    

# Procurement workflow templates
WORKFLOW_TEMPLATES = {
    "buy": {
        "name": "Buy/Purchase Assistant",
        "description": "Helps users purchase goods or services within an organization",
        "stages": [
            "Intent Capture - Understand what user wants to buy",
            "Smart Item Discovery - Search catalog, past POs, punchouts",
            "Item Selection & Path Decision - User reviews and decides",
            "Standard Purchase Path - For catalog items",
            "Custom Request Path - For items not found",
            "Pre-Purchase Validation - Ensure compliance",
            "Purchase Execution - Create requisition/PO"
        ],
        "tools": [
            {"name": "catalog_search", "purpose": "Search product catalog"},
            {"name": "past_po_search", "purpose": "Search past purchase orders"},
            {"name": "punchout_search", "purpose": "Search external catalogs"},
            {"name": "supplier_validate", "purpose": "Validate supplier status"},
            {"name": "requisition_create", "purpose": "Create purchase requisition"},
        ]
    },
    "invoice": {
        "name": "Invoice Processing Assistant",
        "description": "Processes invoices with 2-way/3-way matching and exception handling",
        "stages": [
            "Invoice Capture - Upload or receive invoice",
            "Data Extraction - OCR and parse invoice data",
            "PO/GRN Matching - 2-way or 3-way matching",
            "Exception Detection - Identify discrepancies",
            "Exception Resolution - Handle pricing/quantity issues",
            "Approval Routing - Route for approval based on value",
            "Payment Processing - Schedule payment"
        ],
        "tools": [
            {"name": "invoice_ocr", "purpose": "Extract data from invoice"},
            {"name": "po_lookup", "purpose": "Find matching purchase order"},
            {"name": "grn_lookup", "purpose": "Find goods receipt note"},
            {"name": "invoice_match", "purpose": "Perform 2/3-way matching"},
            {"name": "exception_create", "purpose": "Create exception ticket"},
            {"name": "payment_schedule", "purpose": "Schedule payment"},
        ]
    },
    "sourcing": {
        "name": "Sourcing Assistant",
        "description": "Manages RFx events, supplier discovery, and bid evaluation",
        "stages": [
            "Requirement Definition - Capture sourcing needs",
            "Supplier Discovery - Find qualified suppliers",
            "RFx Creation - Create RFP/RFQ/RFI",
            "Bid Collection - Receive and track bids",
            "Bid Evaluation - Score and compare bids",
            "Negotiation Support - Assist with negotiations",
            "Award & Contract - Finalize supplier selection"
        ],
        "tools": [
            {"name": "supplier_search", "purpose": "Search supplier database"},
            {"name": "rfx_create", "purpose": "Create RFP/RFQ/RFI"},
            {"name": "bid_collect", "purpose": "Collect supplier bids"},
            {"name": "bid_evaluate", "purpose": "Score and rank bids"},
            {"name": "contract_create", "purpose": "Generate contract"},
        ]
    },
    "contract": {
        "name": "Contract Management Assistant",
        "description": "Manages contract lifecycle, renewals, and compliance",
        "stages": [
            "Contract Request - Capture contract needs",
            "Template Selection - Choose appropriate template",
            "Contract Drafting - Generate contract draft",
            "Review & Negotiation - Track redlines and approvals",
            "Execution - Manage signatures",
            "Compliance Monitoring - Track obligations",
            "Renewal Management - Handle expirations"
        ],
        "tools": [
            {"name": "template_search", "purpose": "Find contract templates"},
            {"name": "contract_draft", "purpose": "Generate contract"},
            {"name": "redline_track", "purpose": "Track changes"},
            {"name": "signature_request", "purpose": "Request e-signatures"},
            {"name": "obligation_track", "purpose": "Track compliance"},
        ]
    },
    "supplier": {
        "name": "Supplier Management Assistant",
        "description": "Manages supplier onboarding, performance, and risk",
        "stages": [
            "Supplier Request - New supplier registration",
            "Due Diligence - Background and compliance checks",
            "Qualification - Evaluate supplier capabilities",
            "Onboarding - Complete registration and setup",
            "Performance Monitoring - Track KPIs and SLAs",
            "Risk Assessment - Identify and monitor risks",
            "Relationship Management - Manage ongoing relationship"
        ],
        "tools": [
            {"name": "supplier_register", "purpose": "Register new supplier"},
            {"name": "compliance_check", "purpose": "Run compliance checks"},
            {"name": "performance_score", "purpose": "Calculate performance"},
            {"name": "risk_assess", "purpose": "Assess supplier risk"},
        ]
    },
    "receiving": {
        "name": "Goods Receipt Assistant",
        "description": "Manages goods receipt, inspection, and inventory updates",
        "stages": [
            "Delivery Notification - Receive ASN or delivery notice",
            "Receipt Capture - Record goods arrival",
            "Inspection - Quality check if required",
            "Discrepancy Handling - Handle shortages/damages",
            "GRN Creation - Create goods receipt note",
            "Inventory Update - Update stock levels",
            "Invoice Trigger - Notify AP for payment"
        ],
        "tools": [
            {"name": "asn_lookup", "purpose": "Find advance shipping notice"},
            {"name": "grn_create", "purpose": "Create goods receipt"},
            {"name": "inspection_record", "purpose": "Record inspection results"},
            {"name": "inventory_update", "purpose": "Update inventory"},
        ]
    },
    "custom": {
        "name": "Custom Workflow",
        "description": "Define your own procurement workflow from scratch",
        "stages": [],
        "tools": []
    }
}


class EnhancedWorkflowCreator:
    """Enhanced workflow creator with LibreChat-style experience."""
    
    def __init__(self, llm_client=None):
        self.llm = llm_client
        self.state = WorkflowState()
        self.session_id = str(uuid4())
    
    def get_welcome_message(self) -> str:
        """Generate welcome message."""
        return """# 🎯 Procurement Agent Creator

Welcome! I'll help you create a production-ready AI agent for your procurement workflow.

**What I can help you build:**
- 🛒 **Buy/Purchase Assistants** - Help users procure goods & services
- 📄 **Invoice Processing** - 2-way/3-way matching, exceptions
- 🔍 **Sourcing Assistants** - RFx, bid evaluation, supplier discovery
- 📝 **Contract Management** - Lifecycle, renewals, compliance
- 👥 **Supplier Management** - Onboarding, performance, risk
- 📦 **Goods Receipt** - Receiving, inspection, inventory
- ⚙️ **Custom Workflows** - Build your own from scratch

---

## Step 1: What type of procurement workflow do you want to create?

**[1]** 🛒 Buy/Purchase Assistant
**[2]** 📄 Invoice Processing Assistant  
**[3]** 🔍 Sourcing Assistant
**[4]** 📝 Contract Management Assistant
**[5]** 👥 Supplier Management Assistant
**[6]** 📦 Goods Receipt Assistant
**[7]** ⚙️ Custom Workflow

*Reply with a number (1-7) or describe what you want to build*"""

    def process_message(self, user_message: str, history: List) -> tuple:
        """Process user message based on current state."""
        history = history or []
        
        if not user_message.strip():
            return history, self._get_current_state_display()
        
        # Add user message
        history.append({"role": "user", "content": user_message})
        
        # Process based on current step
        response = self._handle_step(user_message)
        
        # Add assistant response
        history.append({"role": "assistant", "content": response})
        
        return history, self._get_current_state_display()
    
    def _handle_step(self, user_input: str) -> str:
        """Handle user input based on current workflow step."""
        
        if self.state.step == WorkflowStep.WELCOME:
            return self._handle_workflow_type_selection(user_input)
        
        elif self.state.step == WorkflowStep.WORKFLOW_TYPE:
            return self._handle_workflow_type_selection(user_input)
        
        elif self.state.step == WorkflowStep.EXPERIENCE_LEVEL:
            return self._handle_experience_level(user_input)
        
        elif self.state.step == WorkflowStep.HIGH_LEVEL_WORKFLOW:
            return self._handle_workflow_stages(user_input)
        
        elif self.state.step == WorkflowStep.WORKFLOW_CONFIRMATION:
            return self._handle_workflow_confirmation(user_input)
        
        elif self.state.step == WorkflowStep.DETAIL_GATHERING:
            return self._handle_detail_gathering(user_input)
        
        elif self.state.step == WorkflowStep.TOOL_IDENTIFICATION:
            return self._handle_tool_identification(user_input)
        
        elif self.state.step == WorkflowStep.BUNDLE_NAMING:
            return self._handle_bundle_naming(user_input)
        
        elif self.state.step == WorkflowStep.FINAL_REVIEW:
            return self._handle_final_review(user_input)
        
        elif self.state.step == WorkflowStep.GENERATION:
            return self._generate_output()
        
        else:
            return self._handle_general_input(user_input)
    
    def _handle_workflow_type_selection(self, user_input: str) -> str:
        """Handle workflow type selection."""
        input_lower = user_input.lower().strip()
        
        # Map inputs to workflow types
        type_map = {
            "1": "buy", "buy": "buy", "purchase": "buy", "procurement": "buy",
            "2": "invoice", "invoice": "invoice", "ap": "invoice", "accounts payable": "invoice",
            "3": "sourcing", "sourcing": "sourcing", "rfp": "sourcing", "rfq": "sourcing",
            "4": "contract", "contract": "contract",
            "5": "supplier", "supplier": "supplier", "vendor": "supplier",
            "6": "receiving", "receiving": "receiving", "goods receipt": "receiving", "grn": "receiving",
            "7": "custom", "custom": "custom",
        }
        
        workflow_type = None
        for key, value in type_map.items():
            if key in input_lower:
                workflow_type = value
                break
        
        if not workflow_type:
            # Use LLM to understand intent if available
            if self.llm:
                workflow_type = self._infer_workflow_type(user_input)
            else:
                workflow_type = "custom"
        
        self.state.workflow_type = workflow_type
        template = WORKFLOW_TEMPLATES.get(workflow_type, WORKFLOW_TEMPLATES["custom"])
        self.state.workflow_name = template["name"]
        self.state.description = user_input if workflow_type == "custom" else template["description"]
        self.state.workflow_stages = template["stages"].copy()
        self.state.tools_identified = template["tools"].copy()
        
        self.state.step = WorkflowStep.EXPERIENCE_LEVEL
        
        return f"""✅ **Got it!** You want to create a **{template['name']}**

{template['description']}

---

## Step 2: Agent Experience Preference

How would you like your agent to interact with users?

**[1]** 🔒 **GUIDED** - *"Frequent confirmations and clear checkpoints"*
> Best for: Financial approvals, regulatory compliance, sensitive operations
> Agent asks before every significant action

**[2]** ⚖️ **BALANCED** ⭐ *(Recommended)*
> Best for: General procurement workflows, standard operations
> Agent handles routine steps but confirms at key decisions

**[3]** 🚀 **AUTONOMOUS** - *"Work independently, check in when needed"*
> Best for: Research, exploration, routine tasks
> Agent works mostly on its own

*Which experience level do you prefer? [1, 2, or 3]*"""

    def _handle_experience_level(self, user_input: str) -> str:
        """Handle experience level selection."""
        input_lower = user_input.lower().strip()
        
        if "1" in input_lower or "guided" in input_lower:
            self.state.experience_level = "guided"
            level_name = "GUIDED"
        elif "3" in input_lower or "autonomous" in input_lower:
            self.state.experience_level = "autonomous"
            level_name = "AUTONOMOUS"
        else:
            self.state.experience_level = "balanced"
            level_name = "BALANCED"
        
        self.state.step = WorkflowStep.HIGH_LEVEL_WORKFLOW
        
        # Generate workflow stages display
        stages_display = self._format_workflow_stages()
        
        return f"""✅ **Experience Level:** {level_name}

---

## Step 3: High-Level Workflow

Based on your selection, here's the proposed workflow:

{stages_display}

---

**Does this workflow cover your needs?**
- Reply **"yes"** or **"confirm"** to proceed
- Or describe any changes you'd like to make
- You can also provide a completely different workflow (3-7 stages)"""

    def _format_workflow_stages(self) -> str:
        """Format workflow stages for display."""
        if not self.state.workflow_stages:
            return "*No stages defined yet. Please describe your workflow.*"
        
        lines = ["```mermaid", "flowchart TD"]
        
        for i, stage in enumerate(self.state.workflow_stages, 1):
            stage_name = stage.split(" - ")[0] if " - " in stage else stage
            lines.append(f"    S{i}[Step {i}: {stage_name}]")
        
        # Add connections
        for i in range(1, len(self.state.workflow_stages)):
            lines.append(f"    S{i} --> S{i+1}")
        
        lines.append("```")
        lines.append("")
        lines.append("**Workflow Stages:**")
        
        for i, stage in enumerate(self.state.workflow_stages, 1):
            lines.append(f"{i}. **{stage}**")
        
        return "\n".join(lines)

    def _handle_workflow_stages(self, user_input: str) -> str:
        """Handle workflow stages confirmation or modification."""
        input_lower = user_input.lower().strip()
        
        if input_lower in ["yes", "confirm", "ok", "looks good", "proceed"]:
            self.state.step = WorkflowStep.DETAIL_GATHERING
            return self._ask_detail_questions()
        
        # User wants to modify - use LLM if available
        if self.llm:
            modified_stages = self._refine_workflow_with_llm(user_input)
            if modified_stages:
                self.state.workflow_stages = modified_stages
        else:
            # Parse user input for stages
            if "," in user_input or "\n" in user_input:
                stages = [s.strip() for s in user_input.replace("\n", ",").split(",") if s.strip()]
                if stages:
                    self.state.workflow_stages = stages
        
        stages_display = self._format_workflow_stages()
        
        return f"""✅ **Workflow Updated!**

{stages_display}

---

**Does this look correct now?**
- Reply **"yes"** to proceed
- Or continue making changes"""

    def _ask_detail_questions(self) -> str:
        """Ask detailed questions about the workflow."""
        template = WORKFLOW_TEMPLATES.get(self.state.workflow_type, {})
        
        questions = []
        
        if self.state.workflow_type == "buy":
            questions = [
                "What sources should the agent search? (catalog, past POs, punchouts, all)",
                "Should it support vendor quote uploads?",
                "What approval thresholds apply? (e.g., >$10K needs manager approval)",
            ]
        elif self.state.workflow_type == "invoice":
            questions = [
                "What matching type? (2-way PO-Invoice, or 3-way PO-GRN-Invoice)",
                "What tolerance % for price/quantity discrepancies?",
                "How should exceptions be routed?",
            ]
        elif self.state.workflow_type == "sourcing":
            questions = [
                "What RFx types? (RFP, RFQ, RFI, all)",
                "How should bids be evaluated? (price-only, weighted scoring)",
                "Auction support needed?",
            ]
        else:
            questions = [
                "Who are the target users? (employees, managers, buyers)",
                "What validations are required?",
                "What systems should it integrate with?",
            ]
        
        self.state.step = WorkflowStep.TOOL_IDENTIFICATION
        
        return f"""## Step 4: Workflow Details

Let me understand the specifics:

{chr(10).join([f'**Q{i+1}:** {q}' for i, q in enumerate(questions)])}

*Please answer these questions, or say "skip" to use defaults*"""

    def _handle_detail_gathering(self, user_input: str) -> str:
        """Handle detail gathering responses."""
        if user_input.lower().strip() != "skip":
            self.state.custom_requirements.append(user_input)
        
        self.state.step = WorkflowStep.TOOL_IDENTIFICATION
        return self._show_tools()

    def _handle_tool_identification(self, user_input: str) -> str:
        """Handle tool identification."""
        input_lower = user_input.lower().strip()
        
        if input_lower in ["yes", "confirm", "ok", "proceed"]:
            self.state.step = WorkflowStep.BUNDLE_NAMING
            return self._ask_bundle_name()
        
        # User wants to add/modify tools
        self.state.custom_requirements.append(f"Tool request: {user_input}")
        return self._show_tools() + "\n\n*Any other tools needed? Reply 'yes' to proceed*"

    def _show_tools(self) -> str:
        """Show identified tools."""
        tools_display = "\n".join([
            f"- **{t['name']}** - {t['purpose']}" 
            for t in self.state.tools_identified
        ])
        
        return f"""## Step 5: Tools Identification

Based on your workflow, these tools are needed:

{tools_display}

---

**Tool Classification:**
- 🟡 **SUBTOOL** - Atomic operations (API calls, simple validations)
- 🔵 **SUB-AGENT** - Context-aware reasoning (recommendations, analysis)

*Is this tool list complete? Reply 'yes' or add more tools*"""

    def _ask_bundle_name(self) -> str:
        """Ask for bundle name."""
        suggested_name = self.state.workflow_type + "_assistant@ORG#v1.0"
        
        return f"""## Step 6: Bundle Naming

Your agent needs a unique identifier.

**Suggested Name:** `{suggested_name}`

*Accept this name or provide your own (format: name@ORG#version)*"""

    def _handle_bundle_naming(self, user_input: str) -> str:
        """Handle bundle naming."""
        if user_input.lower().strip() in ["yes", "ok", "accept"]:
            self.state.bundle_name = self.state.workflow_type + "_assistant@ORG#v1.0"
        else:
            self.state.bundle_name = user_input.strip()
        
        self.state.step = WorkflowStep.FINAL_REVIEW
        return self._show_final_review()

    def _show_final_review(self) -> str:
        """Show final review before generation."""
        stages_list = "\n".join([f"   {i+1}. {s}" for i, s in enumerate(self.state.workflow_stages)])
        tools_list = "\n".join([f"   - {t['name']}" for t in self.state.tools_identified])
        
        return f"""## 📋 Final Review

**Bundle Name:** `{self.state.bundle_name}`
**Workflow Type:** {self.state.workflow_name}
**Experience Level:** {self.state.experience_level.upper()}

**Description:**
{self.state.description}

**Workflow Stages:**
{stages_list}

**Tools:**
{tools_list}

---

**Ready to generate?**
- Reply **"generate"** to create your agent
- Or describe any final changes"""

    def _handle_final_review(self, user_input: str) -> str:
        """Handle final review confirmation."""
        input_lower = user_input.lower().strip()
        
        if input_lower in ["generate", "yes", "create", "build", "go"]:
            self.state.step = WorkflowStep.GENERATION
            return self._generate_output()
        
        return "What would you like to change?"

    def _generate_output(self) -> str:
        """Generate the final output."""
        self.state.step = WorkflowStep.COMPLETE
        
        # Use LLM to generate the prompt if available
        if self.llm:
            prompt = self._generate_with_llm()
        else:
            prompt = self._generate_template_prompt()
        
        return f"""# 🎉 Agent Created Successfully!

## ✅ Bundle: `{self.state.bundle_name}`

### 📊 Summary

| Property | Value |
|----------|-------|
| **Name** | {self.state.workflow_name} |
| **Type** | {self.state.workflow_type} |
| **Experience** | {self.state.experience_level} |
| **Stages** | {len(self.state.workflow_stages)} |
| **Tools** | {len(self.state.tools_identified)} |

### 🔄 Workflow Diagram

```mermaid
flowchart TD
{self._generate_mermaid_diagram()}
```

### 📄 Generated System Prompt

<details>
<summary>Click to expand full prompt</summary>

```markdown
{prompt[:3000]}...
```

</details>

---

**🚀 What's Next?**
1. Download the generated prompt
2. Configure the tools in your system
3. Test with sample scenarios
4. Deploy to production

*Would you like to:*
- **[1]** Download the full prompt
- **[2]** Modify the workflow
- **[3]** Create another agent"""

    def _generate_mermaid_diagram(self) -> str:
        """Generate Mermaid diagram code."""
        lines = []
        for i, stage in enumerate(self.state.workflow_stages, 1):
            stage_name = stage.split(" - ")[0] if " - " in stage else stage[:30]
            lines.append(f"    S{i}[\"{stage_name}\"]")
        
        for i in range(1, len(self.state.workflow_stages)):
            lines.append(f"    S{i} --> S{i+1}")
        
        return "\n".join(lines)

    def _generate_template_prompt(self) -> str:
        """Generate a template-based prompt."""
        stages_text = "\n\n".join([
            f"### STEP_{i:02d}: {stage}\n- **Purpose**: {stage.split(' - ')[1] if ' - ' in stage else 'Execute this step'}\n- **Tool(s)**: See tool reference\n- **Routing**: Proceed to next step"
            for i, stage in enumerate(self.state.workflow_stages, 1)
        ])
        
        tools_text = "\n".join([
            f"- **{t['name']}**: {t['purpose']}"
            for t in self.state.tools_identified
        ])
        
        return f"""# System Prompt: {self.state.workflow_name}

## System Identity
You are **{self.state.workflow_name}**, an AI assistant designed to help users with {self.state.workflow_type} workflows in a procurement context.

## Core Rules
1. Follow the workflow steps in order
2. Use tools before responding with data
3. Confirm important decisions with users
4. Never bypass compliance checks

## Guardrails
1. **NEVER** skip validation steps
2. **NEVER** process without required approvals
3. **ALWAYS** use appropriate tools
4. **ALWAYS** maintain audit trail

## Workflow Steps

{stages_text}

## Available Tools

{tools_text}

## Tool Discipline
1. **NEVER** respond with data without calling the appropriate tool first
2. **ALWAYS** validate tool responses before presenting to user
3. **ALWAYS** log significant actions

## Experience Level: {self.state.experience_level.upper()}
{"Confirm every significant action" if self.state.experience_level == "guided" else "Confirm at key decision points" if self.state.experience_level == "balanced" else "Work independently, check in when needed"}
"""

    def _generate_with_llm(self) -> str:
        """Generate prompt using LLM."""
        try:
            system_prompt = """You are a System Prompt Architect for procurement AI agents.
Generate a complete, production-ready system prompt based on the specification provided.
Include: System Identity, Core Rules, Guardrails (NEVER/ALWAYS), Workflow Steps, Tools, Error Handling."""
            
            user_prompt = f"""Generate a system prompt for:

Name: {self.state.workflow_name}
Type: {self.state.workflow_type}
Experience: {self.state.experience_level}
Description: {self.state.description}

Workflow Stages:
{json.dumps(self.state.workflow_stages, indent=2)}

Tools:
{json.dumps(self.state.tools_identified, indent=2)}

Custom Requirements:
{json.dumps(self.state.custom_requirements, indent=2)}
"""
            
            response = self.llm.generate_simple(
                system_prompt=system_prompt,
                user_message=user_prompt,
                temperature=0.2
            )
            return response
        except Exception as e:
            return self._generate_template_prompt()

    def _infer_workflow_type(self, user_input: str) -> str:
        """Use LLM to infer workflow type."""
        try:
            response = self.llm.generate_simple(
                system_prompt="You are a procurement domain expert. Classify the user's request into one of: buy, invoice, sourcing, contract, supplier, receiving, custom. Respond with just the category name.",
                user_message=user_input,
                temperature=0.0
            )
            return response.strip().lower()
        except:
            return "custom"

    def _refine_workflow_with_llm(self, user_input: str) -> List[str]:
        """Refine workflow stages using LLM."""
        try:
            response = self.llm.generate_simple(
                system_prompt="You are a procurement workflow designer. Given the user's feedback, generate a refined list of workflow stages (3-7 stages). Return as a JSON array of strings.",
                user_message=f"Current stages: {self.state.workflow_stages}\n\nUser feedback: {user_input}",
                temperature=0.2
            )
            import re
            match = re.search(r'\[.*\]', response, re.DOTALL)
            if match:
                return json.loads(match.group())
        except:
            pass
        return []

    def _get_current_state_display(self) -> str:
        """Get current state for sidebar display."""
        steps_status = {
            WorkflowStep.WELCOME: "🔵",
            WorkflowStep.WORKFLOW_TYPE: "🔵" if self.state.step.value > WorkflowStep.WORKFLOW_TYPE.value else "⚪",
            WorkflowStep.EXPERIENCE_LEVEL: "🔵" if self.state.step.value > WorkflowStep.EXPERIENCE_LEVEL.value else "⚪",
            WorkflowStep.HIGH_LEVEL_WORKFLOW: "🔵" if self.state.step.value > WorkflowStep.HIGH_LEVEL_WORKFLOW.value else "⚪",
            WorkflowStep.TOOL_IDENTIFICATION: "🔵" if self.state.step.value > WorkflowStep.TOOL_IDENTIFICATION.value else "⚪",
            WorkflowStep.BUNDLE_NAMING: "🔵" if self.state.step.value > WorkflowStep.BUNDLE_NAMING.value else "⚪",
            WorkflowStep.FINAL_REVIEW: "🔵" if self.state.step.value > WorkflowStep.FINAL_REVIEW.value else "⚪",
            WorkflowStep.COMPLETE: "✅" if self.state.step == WorkflowStep.COMPLETE else "⚪",
        }
        
        return f"""## 📊 Progress

{steps_status.get(WorkflowStep.WORKFLOW_TYPE, '⚪')} **Step 1:** Workflow Type
{steps_status.get(WorkflowStep.EXPERIENCE_LEVEL, '⚪')} **Step 2:** Experience Level
{steps_status.get(WorkflowStep.HIGH_LEVEL_WORKFLOW, '⚪')} **Step 3:** Workflow Design
{steps_status.get(WorkflowStep.TOOL_IDENTIFICATION, '⚪')} **Step 4:** Tool Identification
{steps_status.get(WorkflowStep.BUNDLE_NAMING, '⚪')} **Step 5:** Bundle Naming
{steps_status.get(WorkflowStep.FINAL_REVIEW, '⚪')} **Step 6:** Final Review
{steps_status.get(WorkflowStep.COMPLETE, '⚪')} **Step 7:** Generation

---

**Current Selection:**
- Type: {self.state.workflow_name or 'Not selected'}
- Experience: {self.state.experience_level or 'Not selected'}
- Stages: {len(self.state.workflow_stages)}
- Tools: {len(self.state.tools_identified)}
"""

    def reset(self):
        """Reset the workflow state."""
        self.state = WorkflowState()
        self.session_id = str(uuid4())


def create_enhanced_app(llm_client=None):
    """Create the enhanced Gradio app."""
    creator = EnhancedWorkflowCreator(llm_client=llm_client)
    
    with gr.Blocks(
        title="Procurement Agent Creator",
        css="""
        .chatbot-container { min-height: 500px; }
        .progress-panel { background: #f5f5f5; padding: 15px; border-radius: 8px; }
        """
    ) as app:
        gr.Markdown("""
        # 🤖 Procurement Agent Creator
        ### Create production-ready AI agents for any procurement workflow
        """)
        
        with gr.Row():
            with gr.Column(scale=3):
                chatbot = gr.Chatbot(
                    value=[{"role": "assistant", "content": creator.get_welcome_message()}],
                    height=600,
                    label="Conversation",
                )
                
                with gr.Row():
                    msg_input = gr.Textbox(
                        placeholder="Type your response...",
                        label="Your Message",
                        lines=2,
                        scale=4,
                    )
                    send_btn = gr.Button("Send", variant="primary", scale=1)
                
                with gr.Row():
                    reset_btn = gr.Button("🔄 Start Over", variant="secondary")
            
            with gr.Column(scale=1):
                progress_display = gr.Markdown(
                    value=creator._get_current_state_display(),
                    label="Progress",
                )
        
        # Event handlers
        def on_send(message, history):
            new_history, progress = creator.process_message(message, history)
            return new_history, progress, ""
        
        def on_reset():
            creator.reset()
            return (
                [{"role": "assistant", "content": creator.get_welcome_message()}],
                creator._get_current_state_display(),
            )
        
        send_btn.click(
            fn=on_send,
            inputs=[msg_input, chatbot],
            outputs=[chatbot, progress_display, msg_input],
        )
        
        msg_input.submit(
            fn=on_send,
            inputs=[msg_input, chatbot],
            outputs=[chatbot, progress_display, msg_input],
        )
        
        reset_btn.click(
            fn=on_reset,
            outputs=[chatbot, progress_display],
        )
    
    return app


if __name__ == "__main__":
    app = create_enhanced_app()
    app.launch(server_port=7863)

