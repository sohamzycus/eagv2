# agent.py - supports Gemini (google-genai) and OpenAI-compatible clients; logs raw requests/responses
import os, json, time, logging, argparse, requests
from utils import setup_logging, log_and_time
from prompt_manager import system_prompt_text, plan_calls as deterministic_plan

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv not available, use system environment variables

setup_logging()
logger = logging.getLogger('agent')

class GeminiClient:
    def __init__(self):
        # Prefer google genai if available and GOOGLE_API_KEY is set
        self.mode = None
        self.client = None
        self.api_key = os.environ.get('GOOGLE_API_KEY') or os.environ.get('GEMINI_API_KEY')
        
        # No hardcoded API key - environment variables or .env file required
        if not self.api_key:
            logger.error('No API key found. Please set GOOGLE_API_KEY or GEMINI_API_KEY in .env file or environment variables.')
            logger.info('Create a .env file with: GOOGLE_API_KEY=your_api_key_here')
        if self.api_key:
            try:
                from google import genai
                self.client = genai.Client(api_key=self.api_key)
                self.mode = 'google_genai'
            except Exception as e:
                logger.warning('google-genai not available: %s', e)
                self.client = None
        # fallback to OpenAI-compatible (if OPENAI_API_KEY present)
        if self.client is None and os.environ.get('OPENAI_API_KEY'):
            try:
                import openai
                openai.api_key = os.environ.get('OPENAI_API_KEY')
                self.client = openai
                self.mode = 'openai_compat'
            except Exception as e:
                logger.warning('openai package not available: %s', e)
                self.client = None
        if self.client is None:
            logger.info('No LLM client initialized; using deterministic planner as stub')

    def generate(self, system_prompt, user_message):
        """Return dict with raw_request, raw_response_text, tool_calls (parsed), and content."""
        if self.mode == 'google_genai':
            # Using google.genai Client -> models.generate_content
            # Create a proper message with system prompt
            full_message = f"{system_prompt}\n\nUser Request: {user_message}\n\nRespond with TOOL_CALL lines only:"
            raw_request = {'model':'gemini-2.0-flash','contents': full_message}
            logger.info('Calling Google GenAI with model gemini-2.0-flash')
            resp = self.client.models.generate_content(model='gemini-2.0-flash', contents=full_message)
            raw_response_text = getattr(resp, 'text', str(resp))
            # NOTE: parsing tool calls from raw_response_text is application-specific.
            # Here we assume the model returns a sequence of TOOL_CALL lines as in our system prompt.
            parsed_calls = self._parse_tool_calls(raw_response_text)
            return {'raw_request': raw_request, 'raw_response': resp, 'raw_response_text': raw_response_text, 'tool_calls': parsed_calls, 'content': raw_response_text}
        elif self.mode == 'openai_compat':
            # call the OpenAI Chat/completions API compatibly if user has set OPENAI_API_KEY
            raw_request = {'model':'gemini-2.0-flash','messages':[{'role':'system','content': system_prompt},{'role':'user','content': user_message}]}
            logger.info('Calling OpenAI-compatible API with model gemini-2.0-flash')
            resp = self.client.ChatCompletion.create(model='gemini-2.0-flash', messages=raw_request['messages'])
            raw_response_text = resp.choices[0].message.content
            parsed_calls = self._parse_tool_calls(raw_response_text)
            return {'raw_request': raw_request, 'raw_response': resp, 'raw_response_text': raw_response_text, 'tool_calls': parsed_calls, 'content': raw_response_text}
        else:
            # stub deterministic planner
            calls, log_line = deterministic_plan(user_message)
            # model "response" text
            resp_text = '\n'.join([f'TOOL_CALL: {name} {json.dumps(payload)}' for name,payload in calls])
            return {'raw_request': None, 'raw_response': None, 'raw_response_text': resp_text, 'tool_calls': calls, 'content': resp_text}

    def _parse_tool_calls(self, text):
        """Parse lines starting with TOOL_CALL: into (name, payload dict)."""
        calls = []
        for line in text.splitlines():
            line = line.strip()
            if line.startswith('TOOL_CALL:'):
                rest = line[len('TOOL_CALL:'):].strip()
                # expect format: <name> <json_payload>
                try:
                    name, payload_json = rest.split(' ',1)
                    payload = json.loads(payload_json)
                except Exception:
                    # fallback: if it's just the tool name and no json, treat payload as {}
                    try:
                        name = rest.strip()
                        payload = {}
                    except Exception:
                        continue
                calls.append((name, payload))
        return calls

@log_and_time
def run_agent(user_question: str, server_url: str, session_output: str='llm_session.json', timeout: int=30):
    system_prompt = system_prompt_text()
    session = {'system_prompt': system_prompt, 'messages': [{'role':'user','content':user_question}], 'llm_raw_request': None, 'llm_raw_response': None, 'tool_execution': [], 'timestamp': time.time()}
    client = GeminiClient()
    gen = client.generate(system_prompt, user_question)
    session['llm_raw_request'] = gen.get('raw_request')
    # We store raw_response as JSON-serializable if possible; otherwise str()
    try:
        session['llm_raw_response'] = gen.get('raw_response_text') or str(gen.get('raw_response'))
    except Exception:
        session['llm_raw_response'] = str(gen.get('raw_response'))
    logger.info('LLM raw response:\n%s', session['llm_raw_response'])

    # Execute tool calls sequentially
    for name, payload in gen.get('tool_calls', []):
        if name == 'get_monitor_info':
            resp = requests.post(f'{server_url}/tool/get_monitor_info', json=payload, timeout=timeout); res_json = resp.json()
            session['tool_execution'].append({'tool': name, 'payload': payload, 'response': res_json})
            monitor_info = {'monitors': res_json.get('monitors'), 'primary': res_json.get('primary',0)}
        elif name == 'open_paint':
            resp = requests.post(f'{server_url}/tool/open_paint', json=payload, timeout=timeout); res_json = resp.json()
            session['tool_execution'].append({'tool': name, 'payload': payload, 'response': res_json})
            if res_json.get('status') != 'ok': break
        elif name == 'draw_rectangle':
            resp = requests.post(f'{server_url}/tool/draw_rectangle', json=payload, timeout=timeout); res_json = resp.json()
            session['tool_execution'].append({'tool': name, 'payload': payload, 'response': res_json})
            if res_json.get('status') != 'ok': break
        elif name == 'add_text_in_paint':
            resp = requests.post(f'{server_url}/tool/add_text_in_paint', json=payload, timeout=timeout); res_json = resp.json()
            session['tool_execution'].append({'tool': name, 'payload': payload, 'response': res_json})
            if res_json.get('status') != 'ok': break
        else:
            logger.warning('Unknown tool: %s', name)
    # Save session
    with open(session_output, 'w', encoding='utf-8') as fh: json.dump(session, fh, indent=2)
    logger.info('Saved session to %s', session_output)
    return session

if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('--server', default='http://127.0.0.1:5000'); parser.add_argument('--question', default='What are you doing? Learning that prompting really is the key!'); parser.add_argument('--out', default='llm_session.json'); args = parser.parse_args(); run_agent(args.question, args.server, args.out)
