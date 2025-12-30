---
title: Procurement Workflow Agent Creator
emoji: 🤖
colorFrom: blue
colorTo: purple
sdk: gradio
sdk_version: 5.9.1
app_file: app.py
pinned: false
license: mit
---

# 🤖 Procurement Workflow Agent Creator

**LLM-Powered** AI agent designer for enterprise procurement workflows.

## How It Works

This tool uses **GPT-4o** as its core engine to:

1. **Understand** your business requirements through natural conversation
2. **Design** intelligent workflow stages with proper sequencing
3. **Identify** required tools and APIs for each stage
4. **Generate** production-ready system prompts

## Features

- 💬 **Conversational Design** - Describe what you need in plain English
- 🔧 **Tool-Aware Prompts** - Every stage maps to specific tools
- 🔄 **Orchestration Agnostic** - Works with AutoGen, CrewAI, LangGraph
- 🤖 **Model Agnostic** - Generated prompts work with any LLM

## Requirements

**LLM is REQUIRED** - This is not a template tool. The AI actively:
- Understands your unique requirements
- Designs custom workflows
- Generates intelligent prompts

### Environment Variables (Required)

```
AZURE_OPENAI_API_KEY=your_api_key
AZURE_OPENAI_ENDPOINT=your_endpoint
AZURE_OPENAI_DEPLOYMENT=your_deployment
AZURE_OPENAI_VERIFY_SSL=false
```

Add these in Space Settings > Repository secrets

## Quick Start

1. Describe your workflow: *"I need an agent that helps employees buy items and routes approvals based on value"*
2. Refine through conversation
3. Click "Generate Prompt"
4. Export to your preferred format

## Output Formats

- **System Prompt** - Copy to any LLM
- **MCP Tools** - For MCP-compatible servers
- **AutoGen Config** - Direct import format

## Local Development

```bash
# Set environment variables
export AZURE_OPENAI_API_KEY="your-key"

# Install and run
pip install -r requirements.txt
python app.py
```
