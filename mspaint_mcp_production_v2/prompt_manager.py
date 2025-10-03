# prompt_manager.py - system prompt and deterministic planner
from utils import log_and_time

def system_prompt_text():
    return '''You are an AI agent that controls MS Paint through tool calls. You MUST use these tools to complete drawing tasks:

AVAILABLE TOOLS:
- get_monitor_info() - Get screen dimensions and DPI
- open_paint({"app": "Paint", "monitor": 0}) - Open MS Paint application
- draw_rectangle({"x": int, "y": int, "width": int, "height": int, "line_width": int}) - Draw rectangle
- add_text_in_paint({"x": int, "y": int, "text": "string", "font_size": int}) - Add text

CRITICAL RULES:
1) You MUST respond ONLY with tool calls in this format: TOOL_CALL: tool_name {"param": value}
2) NEVER provide text explanations or instructions - only tool calls
3) Always start with: TOOL_CALL: get_monitor_info {}
4) Then: TOOL_CALL: open_paint {"app": "Paint", "monitor": 0}
5) Then: TOOL_CALL: draw_rectangle {"x": 100, "y": 100, "width": 400, "height": 200, "line_width": 3}
6) Finally: TOOL_CALL: add_text_in_paint {"x": 150, "y": 180, "text": "your text here", "font_size": 24}

EXAMPLE OUTPUT:
TOOL_CALL: get_monitor_info {}
TOOL_CALL: open_paint {"app": "Paint", "monitor": 0}
TOOL_CALL: draw_rectangle {"x": 200, "y": 150, "width": 500, "height": 300, "line_width": 4}
TOOL_CALL: add_text_in_paint {"x": 300, "y": 280, "text": "Hello World", "font_size": 28}
'''

@log_and_time
def plan_calls(question_text: str, monitor_info: dict = None):
    if monitor_info is None:
        monitor_info = {'monitors':[{'index':0,'origin_x':0,'origin_y':0,'width':1920,'height':1080,'dpi_scale':1.0}], 'primary':0}
    mon = monitor_info['monitors'][monitor_info['primary']]
    origin_x = mon['origin_x']; origin_y = mon['origin_y']
    width = mon['width']; height = mon['height']
    rect_w = min(1000, width - 200); rect_h = min(400, height - 200)
    top_left_x = origin_x + (width - rect_w)//2; top_left_y = origin_y + (height - rect_h)//2
    font_size = 28
    approx_text_width = int(font_size * 0.6 * len(question_text))
    text_x = top_left_x + max(10, (rect_w - approx_text_width)//2)
    text_y = top_left_y + max(10, (rect_h - int(font_size*1.2))//2)
    calls = [
        ('get_monitor_info', {}),
        ('open_paint', {'app':'Paint','monitor': mon['index']}),
        ('draw_rectangle', {'x': top_left_x, 'y': top_left_y, 'width': rect_w, 'height': rect_h, 'line_width': 6}),
        ('add_text_in_paint', {'x': text_x, 'y': text_y, 'text': question_text, 'font_size': font_size})
    ]
    log_line = f'LOG: Finished drawing rectangle at ({top_left_x},{top_left_y},{rect_w},{rect_h}) with text "{question_text}"'
    return calls, log_line
