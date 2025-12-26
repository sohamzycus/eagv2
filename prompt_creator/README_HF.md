---
title: Prompt Creator - Procurement AI Assistant Generator
emoji: 🤖
colorFrom: blue
colorTo: purple
sdk: gradio
sdk_version: 4.44.0
app_file: app.py
pinned: false
license: mit
---

# 🤖 Prompt Creator

**Generate production-ready AI procurement assistant prompts with minimal input.**

## What It Does

This tool helps you create complete system prompts for procurement AI assistants:

- **Invoice Processing** - 2-way/3-way matching, exceptions, AP integration
- **Purchase Requisitions** - Catalog/non-catalog, approvals, budget checks
- **Sourcing** - RFP/RFQ/RFI, supplier evaluation
- **Contract Management** - Renewals, compliance
- **And more...**

## How to Use

1. **Describe your use case** in plain language
   - Example: "I want to create an invoice processing assistant"
   
2. **Answer a few clarifying questions**
   - The AI asks relevant questions about your specific workflow
   
3. **Get your production-ready prompt**
   - Complete system prompt with steps, guardrails, and tool references
   - MCP-Zero tool specifications

## Features

✅ **LLM-Powered** - Uses Azure OpenAI GPT-4o for intelligent prompt generation  
✅ **Tool-Aware** - Generated prompts include tool references and discipline  
✅ **Domain Expert** - Understands full Source-to-Pay and Procure-to-Pay workflows  
✅ **Production Ready** - Output prompts include STEP ordering, COVE rules, guardrails  

## Configuration

To use with your own Azure OpenAI:

1. Go to **Settings** → **Repository secrets**
2. Add the following secrets:
   - `AZURE_OPENAI_API_KEY`: Your API key
   - `AZURE_OPENAI_ENDPOINT`: Your endpoint URL
   - `AZURE_OPENAI_DEPLOYMENT`: Your deployment name

## Demo Mode

Without API keys, the app runs in demo mode with mock responses.

---

Built with ❤️ using Gradio and Azure OpenAI

