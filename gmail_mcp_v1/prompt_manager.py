# prompt_manager.py - system prompt and deterministic planner for Gmail operations
from utils import log_and_time

def system_prompt_text():
    return '''You are an AI Research Assistant with Gmail capabilities. You can research topics, analyze information, and communicate findings via email.

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

## RESEARCH CAPABILITIES
For research queries, I can:
- Analyze complex topics and provide detailed explanations
- Create structured reports and summaries
- Generate professional correspondence with research findings
- Handle multi-part questions with comprehensive responses
- Provide citations and references when available

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

## EXAMPLES

### Research Query Example:
**USER**: "Research the benefits of renewable energy and email the findings to sustainability@company.com"

**REASONING:**
User wants comprehensive research on renewable energy benefits, then email results.
This is a RESEARCH_QUERY + EMAIL_TASK combination.

**ACTION_PLAN:**
1. Search for current renewable energy benefits
2. Analyze and structure findings
3. Create professional email with research summary
4. Send to specified recipient

**EXECUTION:**
TOOL_CALL: get_gmail_info {}
TOOL_CALL: search_web {"query": "renewable energy benefits 2024 environmental economic"}
TOOL_CALL: send_email {"to": "sustainability@company.com", "subject": "Renewable Energy Benefits Research Summary", "body": "Dear Sustainability Team,\\n\\nI've compiled comprehensive research on renewable energy benefits...\\n\\n**Environmental Benefits:**\\n- Reduced carbon emissions\\n- Decreased air pollution\\n\\n**Economic Benefits:**\\n- Lower long-term costs\\n- Job creation\\n\\nBest regards,\\nAI Research Assistant"}

**VERIFICATION:**
✓ Research query addressed comprehensively
✓ Professional email format used
✓ Recipient specified correctly

### Simple Email Example:
**USER**: "Send a meeting reminder to team@company.com"

**REASONING:**
Direct EMAIL_TASK - send meeting reminder.
Need to create professional reminder email.

**ACTION_PLAN:**
1. Get Gmail info
2. Send meeting reminder email

**EXECUTION:**
TOOL_CALL: get_gmail_info {}
TOOL_CALL: send_email {"to": "team@company.com", "subject": "Meeting Reminder - Tomorrow", "body": "Hi Team,\\n\\nFriendly reminder about our meeting tomorrow.\\n\\nBest regards,\\nAI Assistant"}

**VERIFICATION:**
✓ Meeting reminder sent successfully
✓ Professional tone maintained
'''

@log_and_time
def plan_calls(question_text: str, gmail_info: dict = None):
    """Generate deterministic email tool calls based on the question"""
    if gmail_info is None:
        gmail_info = {'user_email': 'user@example.com', 'authenticated': True}
    
    # Analyze the question to determine intent
    question_lower = question_text.lower()
    
    calls = [('get_gmail_info', {})]
    
    # Determine the primary action based on keywords
    if any(word in question_lower for word in ['send', 'email', 'mail', 'message']):
        # Extract recipient if mentioned
        if 'to ' in question_lower or '@' in question_text:
            # Try to extract email from question
            words = question_text.split()
            recipient = None
            for word in words:
                if '@' in word and '.' in word:
                    recipient = word.strip('.,!?();')
                    break
            
            if not recipient:
                recipient = 'example@email.com'
            
            # Generate subject and body based on question
            if 'subject' in question_lower:
                subject_parts = question_text.split('subject')
                if len(subject_parts) > 1:
                    subject = subject_parts[1].split('and')[0].strip(' "\'')[:50]
                else:
                    subject = "Message from AI Assistant"
            else:
                subject = "Message from AI Assistant"
            
            # Generate body content
            if any(word in question_lower for word in ['test', 'hello', 'hi']):
                body = f"Hello,\\n\\nThis is a test email generated by an AI assistant in response to: '{question_text}'\\n\\nBest regards,\\nAI Assistant"
            else:
                body = f"Hello,\\n\\nI'm writing in response to your request: '{question_text}'\\n\\nPlease let me know if you need any additional information.\\n\\nBest regards,\\nAI Assistant"
            
            # Decide between send or compose based on keywords
            if any(word in question_lower for word in ['draft', 'compose', 'prepare']):
                calls.append(('compose_email', {
                    'to': recipient,
                    'subject': subject,
                    'body': body
                }))
            else:
                calls.append(('send_email', {
                    'to': recipient,
                    'subject': subject,
                    'body': body
                }))
    
    elif any(word in question_lower for word in ['list', 'check', 'show', 'recent', 'inbox']):
        # List recent emails
        max_results = 5
        if 'all' in question_lower:
            max_results = 20
        elif any(str(i) in question_text for i in range(1, 51)):
            # Extract number from question
            import re
            numbers = re.findall(r'\d+', question_text)
            if numbers:
                max_results = min(int(numbers[0]), 50)
        
        calls.append(('list_recent_emails', {'max_results': max_results}))
    
    else:
        # Default: send a general response email
        calls.append(('send_email', {
            'to': 'example@email.com',
            'subject': 'Response from AI Assistant',
            'body': f"Hello,\\n\\nI received your message: '{question_text}'\\n\\nI'm an AI assistant that can help with email operations through Gmail API.\\n\\nBest regards,\\nAI Assistant"
        }))
    
    log_line = f'LOG: Planned {len(calls)} email operations for: "{question_text}"'
    return calls, log_line
