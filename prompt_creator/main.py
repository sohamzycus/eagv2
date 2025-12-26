#!/usr/bin/env python3
"""
Prompt Creator - Main Entry Point

A Prompt-as-a-Product system that generates production-ready AI agent prompts
from minimal business user input.

AZURE OPENAI GPT-4o is used for:
- All agent reasoning
- Prompt generation
- Clarification flow
- Tool synthesis

Usage:
    python main.py [--demo] [--cli] [--port PORT]

Environment Variables:
    AZURE_OPENAI_ENDPOINT: Azure OpenAI endpoint URL
    AZURE_OPENAI_DEPLOYMENT: Azure deployment name
    AZURE_OPENAI_API_KEY: Azure API key
    
    OR (for standard OpenAI):
    OPENAI_API_KEY: OpenAI API key

Options:
    --demo      Run in demo mode (generate sample prompt)
    --cli       Run interactive CLI mode
    --port      Port for Gradio UI (default: 7860)
"""

import argparse
import json
import os
import sys
from pathlib import Path

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    # Load .env from the same directory as main.py
    env_path = Path(__file__).parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)
        print(f"✅ Loaded environment from .env")
    else:
        # Try loading from current working directory
        load_dotenv()
except ImportError:
    pass  # python-dotenv not installed, rely on system env vars

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from prompt_creator.domain.business_intent import (
    BusinessIntent,
    ProcurementChannel,
    RoutingStrategy,
    ComplianceLevel,
)
from prompt_creator.core.llm.llm_config import LLMConfig, LLMProvider, ModelFamily
from prompt_creator.core.llm.llm_factory import LLMFactory
from prompt_creator.core.llm.llm_logger import LLMCallLogger
from prompt_creator.core.agents.agent_factory import AgentFactory, AgentType
from prompt_creator.core.agents.base_agent import AgentContext
from prompt_creator.core.prompt.prompt_builder import PromptDirector
from prompt_creator.core.tools.mcp_zero_adapter import MCPZeroAdapter
from prompt_creator.core.reasoning.reasoning_store import InMemoryReasoningStore, JSONLReasoningStore
from prompt_creator.core.reasoning.audit_logger import AuditLogger


def create_llm_client(config: LLMConfig = None):
    """
    Create LLM client based on configuration or environment.

    Priority:
    1. Provided config
    2. Azure OpenAI (if AZURE_OPENAI_ENDPOINT set)
    3. OpenAI (if OPENAI_API_KEY set)
    4. Mock client (for demo)
    """
    if config:
        return LLMFactory.create(config)

    # Try Azure OpenAI first
    if os.getenv("AZURE_OPENAI_ENDPOINT"):
        print("🔧 Using Azure OpenAI GPT-4o")
        try:
            return LLMFactory.create_azure_gpt4o()
        except Exception as e:
            print(f"   Warning: Could not create Azure client: {e}")

    # Try standard OpenAI
    if os.getenv("OPENAI_API_KEY"):
        print("🔧 Using OpenAI GPT-4o")
        try:
            return LLMFactory.create_openai_gpt4o()
        except Exception as e:
            print(f"   Warning: Could not create OpenAI client: {e}")

    # Fall back to mock
    print("⚠️  No LLM configured - using mock client")
    print("   Set AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_API_KEY for real execution")
    return LLMFactory.create_mock()


def run_demo(llm_client=None):
    """Run a demonstration of prompt generation with LLM."""
    print("=" * 60)
    print("PROMPT CREATOR - DEMO MODE")
    print("=" * 60)
    print()

    # Create LLM client if not provided
    if llm_client is None:
        llm_client = create_llm_client()

    # Display LLM info
    print(f"📡 LLM Provider: {llm_client.provider_name}")
    print(f"📡 LLM Model: {llm_client.model_name}")
    print()

    # Create sample business intent
    print("📝 Creating sample business intent...")
    intent = BusinessIntent(
        use_case_name="Employee Procurement Assistant",
        description="An AI that helps employees raise purchase requests and routes them correctly",
        supports_goods=True,
        supports_services=True,
        enabled_channels=[
            ProcurementChannel.CATALOG,
            ProcurementChannel.NON_CATALOG,
            ProcurementChannel.QUOTE,
        ],
        quote_upload_enabled=True,
        multi_supplier_quotes=True,
        routing_strategy=RoutingStrategy.THRESHOLD_BASED,
        supplier_validation_required=True,
        compliance_level=ComplianceLevel.STRICT,
        ui_silence_required=True,
        message_prefix_enforcement=True,
        summary_generation=True,
    )

    print(f"✅ Intent: {intent.use_case_name}")
    print(f"   Channels: {', '.join(intent.get_enabled_channel_names())}")
    print(f"   Quote Support: {intent.quote_upload_enabled}")
    print(f"   Value Routing: {intent.requires_value_routing()}")
    print()

    # Configure agents with LLM
    reasoning_store = InMemoryReasoningStore()
    AgentFactory.reset()
    factory = AgentFactory.configure(
        llm_client=llm_client,
        reasoning_store=reasoning_store,
    )

    # Create prompt composer agent
    composer = factory.create(AgentType.PROMPT_COMPOSER)

    # Generate prompt using LLM
    print("🔧 Generating system prompt with LLM...")
    context = AgentContext(
        session_id="demo",
        intent=intent,
        llm_client=llm_client,
        reasoning_store=reasoning_store,
    )

    response = composer.execute(context)

    if response.success:
        prompt = context.generated_prompt
        print(f"✅ Prompt generated: {len(prompt):,} characters")
    else:
        print("⚠️  LLM generation failed, using fallback builder...")
        prompt = PromptDirector.build_procurement_prompt(intent)
        print(f"✅ Prompt generated (fallback): {len(prompt):,} characters")

    print()

    # Generate tools
    print("🛠️ Generating MCP-Zero tools...")
    synthesizer = factory.create(AgentType.TOOL_SYNTHESIZER)
    synth_response = synthesizer.execute(context)

    if synth_response.success:
        tools = context.generated_tools
        print(f"✅ Tools generated: {len(tools)} specifications")
    else:
        adapter = MCPZeroAdapter(intent)
        registry = adapter.generate_registry()
        tools = [t.to_mcp_zero_spec() for t in registry.tools]
        print(f"✅ Tools generated (fallback): {len(tools)} specifications")

    print()

    # Save outputs
    output_dir = Path("./demo_output")
    output_dir.mkdir(exist_ok=True)

    prompt_file = output_dir / "system_prompt.md"
    prompt_file.write_text(prompt)
    print(f"📄 Prompt saved to: {prompt_file}")

    tools_file = output_dir / "mcp_zero_tools.json"
    tools_file.write_text(json.dumps(tools, indent=2))
    print(f"📄 Tools saved to: {tools_file}")

    print()
    print("=" * 60)
    print("DEMO COMPLETE")
    print("=" * 60)
    print()

    # Print preview
    print("📋 PROMPT PREVIEW (first 50 lines):")
    print("-" * 40)
    for i, line in enumerate(prompt.splitlines()[:50]):
        print(line)
    print("...")


def run_ui(port: int = 7860, llm_client=None):
    """Run the Gradio UI with LLM execution."""
    try:
        from prompt_creator.ui.gradio_app import create_app

        # Create LLM client if not provided
        if llm_client is None:
            llm_client = create_llm_client()

        print("🚀 Starting Prompt Creator UI...")
        print(f"   Port: {port}")
        print(f"   LLM: {llm_client.provider_name} / {llm_client.model_name}")
        print()

        app = create_app(llm_client=llm_client)
        app.launch(
            server_port=port,
            share=False,
            show_error=True,
        )
    except ImportError as e:
        print(f"❌ Error: {e}")
        print()
        print("To run the UI, install Gradio:")
        print("  pip install gradio")
        sys.exit(1)


def run_cli(llm_client=None):
    """Run interactive CLI mode with LLM execution."""
    from uuid import uuid4

    print("=" * 60)
    print("PROMPT CREATOR - CLI MODE")
    print("=" * 60)
    print()

    # Create LLM client if not provided
    if llm_client is None:
        llm_client = create_llm_client()

    print(f"📡 LLM: {llm_client.provider_name} / {llm_client.model_name}")
    print()
    print("Describe your procurement use case and I'll generate a system prompt.")
    print("Type 'quit' to exit, 'demo' for a sample, or 'help' for commands.")
    print()

    # Initialize
    session_id = str(uuid4())
    reasoning_store = InMemoryReasoningStore()
    llm_logger = LLMCallLogger()
    llm_logger.start_session(session_id)

    # Configure factory with LLM
    AgentFactory.reset()
    factory = AgentFactory.configure(
        llm_client=llm_client,
        reasoning_store=reasoning_store,
    )

    orchestrator = factory.create(AgentType.INTAKE_ORCHESTRATOR)
    clarification = factory.create(AgentType.CLARIFICATION)
    composer = factory.create(AgentType.PROMPT_COMPOSER)
    synthesizer = factory.create(AgentType.TOOL_SYNTHESIZER)

    context = AgentContext(
        session_id=session_id,
        reasoning_store=reasoning_store,
        llm_client=llm_client,
    )

    while True:
        try:
            user_input = input("\n👤 You: ").strip()

            if not user_input:
                continue

            if user_input.lower() == "quit":
                print("\nGoodbye!")
                break

            if user_input.lower() == "demo":
                run_demo(llm_client)
                continue

            if user_input.lower() == "help":
                print("\nCommands:")
                print("  demo  - Run demo with sample intent")
                print("  quit  - Exit the program")
                print("  help  - Show this message")
                continue

            # Process message
            context = context.with_user_input(user_input)
            context.add_to_history("user", user_input)

            # Run orchestrator
            response = orchestrator.execute(context)
            print(f"\n🤖 Assistant: ", end="")

            # Handle different states
            from prompt_creator.core.agents.intake_orchestrator import OrchestratorState

            if orchestrator.current_state == OrchestratorState.CLARIFYING:
                clar_response = clarification.execute(context)
                if clar_response.requires_user_input:
                    print(clar_response.user_message)
                else:
                    if isinstance(clar_response.output, dict) and "intent" in clar_response.output:
                        context.intent = clar_response.output["intent"]
                    print(clar_response.user_message or "Requirements captured!")
                    orchestrator._state = OrchestratorState.COMPOSING_PROMPT

            if orchestrator.current_state == OrchestratorState.COMPOSING_PROMPT and context.intent:
                print("\n⏳ Generating prompt with LLM...", end="")
                comp_response = composer.execute(context)
                if comp_response.success:
                    print(" Done!")
                    orchestrator._state = OrchestratorState.SYNTHESIZING_TOOLS

            if orchestrator.current_state == OrchestratorState.SYNTHESIZING_TOOLS and context.intent:
                print("⏳ Generating tools...", end="")
                synth_response = synthesizer.execute(context)
                if synth_response.success:
                    print(" Done!")
                    orchestrator._state = OrchestratorState.COMPLETE

            if orchestrator.current_state == OrchestratorState.COMPLETE:
                print("\n✅ Generation complete!")
                print(f"   Prompt: {len(context.generated_prompt):,} characters")
                print(f"   Tools: {len(context.generated_tools)} specifications")
                print("\nSave outputs? (y/n): ", end="")

                if input().strip().lower() == "y":
                    output_dir = Path("./cli_output")
                    output_dir.mkdir(exist_ok=True)

                    (output_dir / "system_prompt.md").write_text(context.generated_prompt)
                    (output_dir / "tools.json").write_text(
                        json.dumps(context.generated_tools, indent=2)
                    )
                    print(f"   Saved to: {output_dir}")

                # Reset for new session
                AgentFactory.reset()
                session_id = str(uuid4())
                factory = AgentFactory.configure(
                    llm_client=llm_client,
                    reasoning_store=reasoning_store,
                )
                context = AgentContext(
                    session_id=session_id,
                    reasoning_store=reasoning_store,
                    llm_client=llm_client,
                )
                orchestrator = factory.create(AgentType.INTAKE_ORCHESTRATOR)
                clarification = factory.create(AgentType.CLARIFICATION)
                composer = factory.create(AgentType.PROMPT_COMPOSER)
                synthesizer = factory.create(AgentType.TOOL_SYNTHESIZER)

                print("\n🔄 Ready for new use case!")

        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Prompt Creator - Generate AI procurement assistant prompts",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Environment Variables:
  AZURE_OPENAI_ENDPOINT      Azure OpenAI endpoint URL
  AZURE_OPENAI_DEPLOYMENT    Azure deployment name  
  AZURE_OPENAI_API_KEY       Azure API key
  
  OPENAI_API_KEY             OpenAI API key (alternative to Azure)

Examples:
  # Run with Azure OpenAI
  export AZURE_OPENAI_ENDPOINT="https://your-resource.openai.azure.com/"
  export AZURE_OPENAI_DEPLOYMENT="gpt-4o"
  export AZURE_OPENAI_API_KEY="your-key"
  python main.py

  # Run demo mode
  python main.py --demo
  
  # Run CLI mode
  python main.py --cli
""",
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Run demo mode (generate sample prompt)",
    )
    parser.add_argument(
        "--cli",
        action="store_true",
        help="Run interactive CLI mode",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=7860,
        help="Port for Gradio UI (default: 7860)",
    )
    parser.add_argument(
        "--model",
        type=str,
        default=None,
        help="Model to use (gpt-4o, gpt-4.1, claude-sonnet, etc.)",
    )

    args = parser.parse_args()

    # Create LLM client once
    llm_client = create_llm_client()

    if args.demo:
        run_demo(llm_client)
    elif args.cli:
        run_cli(llm_client)
    else:
        run_ui(args.port, llm_client)


if __name__ == "__main__":
    main()
