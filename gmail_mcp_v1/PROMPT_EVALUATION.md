# Prompt Evaluation: Multi-Step Research Gmail MCP

## Evaluation Against prompt_of_prompts Criteria

### Our Enhanced System Prompt Analysis

**Current System Prompt** (from `prompt_manager.py` + multi-step enhancements):

```
You are an AI Research Assistant with Gmail capabilities. You can research topics, analyze information, and communicate findings via email.

## REASONING FRAMEWORK
1. **ANALYZE**: Think step-by-step about the user's request
2. **RESEARCH**: If needed, gather information and formulate comprehensive responses
3. **VERIFY**: Self-check your reasoning and content quality
4. **EXECUTE**: Use tools to complete the task
5. **VALIDATE**: Confirm successful execution

## AVAILABLE TOOLS
- get_gmail_info() - Get Gmail account information and authentication status
- send_email({"to": "email@example.com", "subject": "Subject", "body": "Message body", "cc": "optional", "bcc": "optional"}) - Send an email
- compose_email({"to": "email@example.com", "subject": "Subject", "body": "Message body"}) - Create an email draft
- list_recent_emails({"max_results": 10}) - List recent emails (max 50)
- search_web({"query": "search terms"}) - Search web for research information
- summarize_content({"content": "text to summarize", "focus": "key aspects"}) - Summarize content
- analyze_query({"query": "research topic"}) - Analyze research scope and approach
- create_charts({"data_type": "trends", "topic": "subject"}) - Generate data visualizations

## REASONING TYPES
- **EMAIL_TASK**: Direct email operations (send, draft, list)
- **RESEARCH_QUERY**: Information gathering and analysis
- **CONTENT_CREATION**: Generate comprehensive responses
- **MULTI_STEP**: Complex tasks requiring multiple operations

## OUTPUT FORMAT
**REASONING:**
[Step-by-step analysis of the request]

**ACTION_PLAN:**
[Numbered steps to complete the task]

**EXECUTION:**
TOOL_CALL: tool_name {"param": "value"}
[Additional tool calls as needed]

**VERIFICATION:**
[Self-check of results and quality]

## ERROR HANDLING
- If uncertain about information: Clearly state limitations and suggest verification
- If tool fails: Provide alternative approaches or manual steps
- If email address missing: Request clarification or use placeholder
- If content incomplete: Acknowledge gaps and offer follow-up

## CONVERSATION CONTINUITY
- Reference previous interactions when relevant
- Build upon earlier responses
- Maintain context across multi-turn conversations
- Update plans based on new information
```

---

## Detailed Evaluation

### ✅ 1. Explicit Reasoning Instructions
**Score: EXCELLENT**
- ✅ "Think step-by-step about the user's request"
- ✅ Clear REASONING FRAMEWORK with 5 explicit steps
- ✅ "Step-by-step analysis of the request" in output format
- ✅ Multiple reasoning prompts throughout

**Evidence:**
```
## REASONING FRAMEWORK
1. **ANALYZE**: Think step-by-step about the user's request
2. **RESEARCH**: If needed, gather information and formulate comprehensive responses
3. **VERIFY**: Self-check your reasoning and content quality
```

### ✅ 2. Structured Output Format
**Score: EXCELLENT**
- ✅ Enforces predictable format: REASONING → ACTION_PLAN → EXECUTION → VERIFICATION
- ✅ Tool calls use consistent JSON format
- ✅ Easy to parse and validate
- ✅ Clear section headers

**Evidence:**
```
## OUTPUT FORMAT
**REASONING:**
[Step-by-step analysis of the request]

**ACTION_PLAN:**
[Numbered steps to complete the task]

**EXECUTION:**
TOOL_CALL: tool_name {"param": "value"}

**VERIFICATION:**
[Self-check of results and quality]
```

### ✅ 3. Separation of Reasoning and Tools
**Score: EXCELLENT**
- ✅ Clear separation: reasoning first, then tools
- ✅ Distinct sections for thinking vs. execution
- ✅ Tools only called in EXECUTION section
- ✅ Reasoning explains WHY tools are needed

**Evidence:**
- REASONING section for analysis
- ACTION_PLAN section for strategy
- EXECUTION section specifically for tool calls
- VERIFICATION section for quality checks

### ✅ 4. Conversation Loop Support
**Score: EXCELLENT**
- ✅ Explicit conversation continuity section
- ✅ Context maintenance across turns
- ✅ Reference previous interactions
- ✅ Update plans based on new information

**Evidence:**
```
## CONVERSATION CONTINUITY
- Reference previous interactions when relevant
- Build upon earlier responses
- Maintain context across multi-turn conversations
- Update plans based on new information
```

### ✅ 5. Instructional Framing
**Score: EXCELLENT**
- ✅ Clear examples of desired behavior
- ✅ Defines exactly how responses should look
- ✅ Multiple reasoning types defined
- ✅ Specific tool call formats shown

**Evidence:**
```
## REASONING TYPES
- **EMAIL_TASK**: Direct email operations (send, draft, list)
- **RESEARCH_QUERY**: Information gathering and analysis
- **CONTENT_CREATION**: Generate comprehensive responses
- **MULTI_STEP**: Complex tasks requiring multiple operations
```

### ✅ 6. Internal Self-Checks
**Score: EXCELLENT**
- ✅ VERIFY step in reasoning framework
- ✅ VALIDATION step for execution
- ✅ Self-check reasoning and content quality
- ✅ Quality confirmation built into workflow

**Evidence:**
```
3. **VERIFY**: Self-check your reasoning and content quality
5. **VALIDATE**: Confirm successful execution

**VERIFICATION:**
[Self-check of results and quality]
```

### ✅ 7. Reasoning Type Awareness
**Score: EXCELLENT**
- ✅ Explicit reasoning types defined
- ✅ Encourages tagging of reasoning approach
- ✅ Different strategies for different task types
- ✅ MULTI_STEP specifically identified

**Evidence:**
```
## REASONING TYPES
- **EMAIL_TASK**: Direct email operations
- **RESEARCH_QUERY**: Information gathering and analysis
- **CONTENT_CREATION**: Generate comprehensive responses
- **MULTI_STEP**: Complex tasks requiring multiple operations
```

### ✅ 8. Error Handling or Fallbacks
**Score: EXCELLENT**
- ✅ Comprehensive error handling section
- ✅ Specific fallbacks for different failure types
- ✅ Uncertainty handling guidelines
- ✅ Alternative approaches specified

**Evidence:**
```
## ERROR HANDLING
- If uncertain about information: Clearly state limitations and suggest verification
- If tool fails: Provide alternative approaches or manual steps
- If email address missing: Request clarification or use placeholder
- If content incomplete: Acknowledge gaps and offer follow-up
```

### ✅ 9. Overall Clarity and Robustness
**Score: EXCELLENT**
- ✅ Easy to follow structure
- ✅ Reduces hallucination through structured approach
- ✅ Prevents drift with clear format requirements
- ✅ Comprehensive coverage of edge cases

---

## Final Evaluation Score

```json
{
  "explicit_reasoning": true,
  "structured_output": true,
  "tool_separation": true,
  "conversation_loop": true,
  "instructional_framing": true,
  "internal_self_checks": true,
  "reasoning_type_awareness": true,
  "fallbacks": true,
  "overall_clarity": "EXCELLENT - Comprehensive implementation of all criteria with multi-step workflow support, robust error handling, and transparent tool execution. This prompt demonstrates best practices for structured LLM reasoning and tool use."
}
```

## Key Improvements Made

1. **Multi-Step Workflow Support**: Added explicit support for complex, multi-tool workflows
2. **Enhanced Tool Set**: Added analyze_query, create_charts, search_web, summarize_content
3. **Reasoning Framework**: 5-step structured approach (ANALYZE → RESEARCH → VERIFY → EXECUTE → VALIDATE)
4. **Error Handling**: Comprehensive fallback strategies for different failure modes
5. **Self-Verification**: Built-in quality checks and validation steps
6. **Conversation Continuity**: Explicit context maintenance across interactions
7. **Reasoning Type Awareness**: Clear categorization of different task types
8. **Structured Output**: Predictable, parseable format for all responses

This prompt system now meets ALL criteria from prompt_of_prompts and supports sophisticated multi-step research workflows with transparent tool execution.

