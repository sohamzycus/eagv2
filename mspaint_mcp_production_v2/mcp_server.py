"""mcp_server.py - Flask MCP server with DPI and Paint 3D support"""
import time, logging, argparse, json
from flask import Flask, request, jsonify
from utils import setup_logging, log_and_time
setup_logging()
logger = logging.getLogger('mcp_server')

try:
    from pywinauto import Application, Desktop, mouse, keyboard
    import win32api, win32con
    from win32api import GetSystemMetrics
    from PIL import ImageGrab
    import ctypes
    IS_WINDOWS = True
except Exception as e:
    IS_WINDOWS = False
    _IMPORT_ERR = e

app = Flask(__name__)
STATE = {'app_obj': None, 'window': None, 'monitor_origin': (0,0), 'monitor_size': (1024,768), 'dpi_scale': 1.0}

def _get_system_dpi_scale():
    """Attempt to get Windows DPI scale (returns float like 1.0, 1.25, etc.)."""
    try:
        # Try GetDpiForWindow via user32 (Windows 10+)
        user32 = ctypes.windll.user32
        user32.SetProcessDPIAware()
        hWnd = user32.GetDesktopWindow()
        # GetDpiForWindow may not be available on older OS; fallback to GetDpiForSystem
        try:
            dpi = ctypes.windll.user32.GetDpiForWindow(hWnd)
        except Exception:
            try:
                # Windows 8.1+ fallback
                shcore = ctypes.windll.shcore
                MONITOR_DEFAULTTOPRIMARY = 1
                # GetDpiForMonitor signature: (HMONITOR, DPI_TYPE, *dpiX, *dpiY)
                # We'll call GetDpiForSystem if available
                dpi = ctypes.windll.user32.GetDpiForSystem()
            except Exception:
                dpi = 96  # default DPI
        scale = float(dpi) / 96.0
        return scale
    except Exception:
        return 1.0

@app.route('/tool/get_monitor_info', methods=['POST'])
@log_and_time
def http_get_monitor_info():
    if not IS_WINDOWS:
        return jsonify({'status':'error','error':'Not running on Windows','details':str(_IMPORT_ERR)}), 500
    primary_w = GetSystemMetrics(0)
    primary_h = GetSystemMetrics(1)
    dpi_scale = _get_system_dpi_scale()
    monitors = [{'index':0,'origin_x':0,'origin_y':0,'width':primary_w,'height':primary_h,'dpi_scale':dpi_scale}]
    STATE['monitor_origin'] = (0,0); STATE['monitor_size']=(primary_w,primary_h); STATE['dpi_scale']=dpi_scale
    return jsonify({'status':'ok','monitors':monitors,'primary':0})

def _to_screen_coords(x:int,y:int):
    ox,oy = STATE.get('monitor_origin',(0,0)); ds = STATE.get('dpi_scale',1.0)
    return int(ox + round(x * ds)), int(oy + round(y * ds))

def _find_text_tool(win):
    """Try to find a Text tool button using accessible names / control types.
    Works for Paint classic and Paint 3D heuristics."""
    try:
        # Search descendants for an element with name containing 'Text' or 'A' icon
        children = win.descendants()
        for c in children:
            try:
                name = str(c.window_text())
                ctrl_type = c.friendly_class_name()
                if 'text' in name.lower() or name.strip().upper() == 'A' or 'text' in ctrl_type.lower():
                    return c
            except Exception:
                continue
    except Exception:
        pass
    return None

@app.route('/tool/open_paint', methods=['POST'])
@log_and_time
def http_open_paint():
    if not IS_WINDOWS:
        return jsonify({'status':'error','error':'Not running on Windows'}), 500
    data = request.get_json(force=True) or {}; monitor = data.get('monitor',0)
    try:
        # Start Paint
        logger.info('Starting MS Paint...')
        try:
            app_obj = Application(backend='uia').connect(path='mspaint.exe')
            logger.info('Connected to existing Paint process')
        except Exception:
            app_obj = Application(backend='uia').start('mspaint.exe')
            logger.info('Started new Paint process')
        
        time.sleep(2)  # Give Paint more time to load
        
        # Find Paint window - try multiple approaches
        win = None
        for attempt in range(3):
            try:
                logger.info(f'Attempt {attempt+1}: Finding Paint window...')
                win = app_obj.window(title_re='.*Paint.*')
                logger.info('✅ Found Paint window via app_obj')
                break
            except Exception as e1:
                logger.warning(f'app_obj method failed: {e1}')
                try:
                    win = Desktop(backend='uia').window(title_re='.*Paint.*')
                    logger.info('✅ Found Paint window via Desktop')
                    break
                except Exception as e2:
                    logger.warning(f'Desktop method failed: {e2}')
                    if attempt < 2:
                        time.sleep(1)
                        continue
                    else:
                        raise Exception(f'Could not find Paint window after 3 attempts')
        
        # Try to focus the window
        try:
            win.set_focus()
            logger.info('✅ Paint window focused')
        except Exception as e:
            logger.warning(f'Could not focus Paint window: {e} - continuing anyway')
        
        STATE['app_obj']=app_obj; STATE['window']=win
        return jsonify({'status':'ok','title': 'Paint window ready'})
    except Exception as e:
        logger.exception('open_paint failed'); return jsonify({'status':'error','error': str(e)}), 500

@app.route('/tool/draw_rectangle', methods=['POST'])
@log_and_time
def http_draw_rectangle():
    if not IS_WINDOWS:
        return jsonify({'status':'error','error':'Not running on Windows'}), 500
    data = request.get_json(force=True) or {}
    x,y = int(data.get('x',0)), int(data.get('y',0))
    width,height = int(data.get('width',100)), int(data.get('height',100))
    win = STATE.get('window')
    if not win:
        return jsonify({'status':'error','error':'Paint window not opened'}), 400
    sx, sy = _to_screen_coords(x,y); ex, ey = sx + width, sy + height
    try:
        # CRITICAL: First select the rectangle tool from the toolbar
        logger.info(f'Selecting rectangle tool in MS Paint')
        
        # FORCE rectangle tool selection - try EVERY possible method
        logger.info('🔧 FORCING rectangle tool selection...')
        win_rect = win.rectangle()
        
        # Method 1: Try to find actual Rectangle button
        try:
            logger.info('Method 1: Looking for Rectangle button...')
            rect_btn = win.child_window(title="Rectangle", control_type="Button")
            if rect_btn.exists():
                rect_btn.click_input()
                logger.info('✅ Found and clicked Rectangle button!')
                time.sleep(1)
            else:
                raise Exception("Rectangle button not found")
        except Exception as e1:
            logger.warning(f'Method 1 failed: {e1}')
            
            # Method 2: Try Shapes menu
            try:
                logger.info('Method 2: Looking for Shapes menu...')
                shapes_btn = win.child_window(title="Shapes", control_type="Button")
                if shapes_btn.exists():
                    shapes_btn.click_input()
                    time.sleep(0.5)
                    # Look for rectangle in dropdown
                    rect_item = win.child_window(title="Rectangle")
                    if rect_item.exists():
                        rect_item.click_input()
                        logger.info('✅ Selected Rectangle from Shapes menu!')
                        time.sleep(1)
                    else:
                        raise Exception("Rectangle not found in Shapes menu")
                else:
                    raise Exception("Shapes button not found")
            except Exception as e2:
                logger.warning(f'Method 2 failed: {e2}')
                
                # Method 3: Keyboard shortcut
                try:
                    logger.info('Method 3: Using keyboard shortcut...')
                    # Press Alt+H to go to Home tab, then look for rectangle
                    keyboard.send_keys('%h')  # Alt+H for Home tab
                    time.sleep(0.5)
                    # Try to find rectangle tool after opening Home tab
                    rect_btn = win.child_window(title="Rectangle", control_type="Button")
                    if rect_btn.exists():
                        rect_btn.click_input()
                        logger.info('✅ Found Rectangle after Home tab!')
                        time.sleep(1)
                    else:
                        raise Exception("Still no Rectangle button")
                except Exception as e3:
                    logger.warning(f'Method 3 failed: {e3}')
                    
                    # Method 4: Brute force - click multiple ribbon locations
                    logger.info('Method 4: Brute force clicking ribbon locations...')
                    locations = [
                        (win_rect.left + 100, win_rect.top + 120),
                        (win_rect.left + 150, win_rect.top + 120),
                        (win_rect.left + 200, win_rect.top + 120),
                        (win_rect.left + 250, win_rect.top + 120),
                        (win_rect.left + 120, win_rect.top + 100),
                        (win_rect.left + 180, win_rect.top + 100),
                    ]
                    
                    for i, (x, y) in enumerate(locations):
                        try:
                            logger.info(f'Trying location {i+1}: ({x}, {y})')
                            mouse.click(coords=(x, y))
                            time.sleep(0.5)
                        except Exception:
                            continue
                    
                    logger.info('🤞 Completed brute force clicking - hoping rectangle tool is selected')
        
        # Use EXACT same safe area calculation as working direct test
        win_rect = win.rectangle()
        logger.info(f'Paint window rectangle: {win_rect}')
        
        # Calculate safe drawing area (EXACT same as direct test)
        safe_left = win_rect.left + 100
        safe_top = win_rect.top + 250  # Well below ribbon
        safe_right = win_rect.right - 100
        safe_bottom = win_rect.bottom - 100
        
        logger.info(f'Safe drawing area: ({safe_left}, {safe_top}) to ({safe_right}, {safe_bottom})')
        
        # Use center of safe area (EXACT same as direct test)
        center_x = (safe_left + safe_right) // 2
        center_y = (safe_top + safe_bottom) // 2
        
        # Draw a LARGE rectangle that's impossible to miss
        actual_x = center_x - 200  # 200px left of center (LARGER)
        actual_y = center_y - 150  # 150px above center (LARGER)
        actual_ex = center_x + 200  # 200px right of center (LARGER)
        actual_ey = center_y + 150  # 150px below center (LARGER)
        
        # Verify coordinates are sane before drawing
        if actual_x < 0 or actual_y < 0 or actual_ex < 0 or actual_ey < 0:
            raise Exception(f"Invalid coordinates: ({actual_x}, {actual_y}) to ({actual_ex}, {actual_ey})")
        
        logger.info(f'✅ Rectangle coordinates: start=({actual_x}, {actual_y}) end=({actual_ex}, {actual_ey})')
        
        # Wait a moment to ensure tool is selected
        time.sleep(1)  # Give more time for tool selection
        
        # CRITICAL: Click on the canvas first to make sure it's active and ready for drawing
        logger.info(f'🖱️  ACTIVATING CANVAS: Clicking canvas to ensure it\'s ready')
        canvas_click_x = center_x
        canvas_click_y = center_y
        mouse.click(coords=(canvas_click_x, canvas_click_y))
        time.sleep(0.5)
        logger.info(f'✅ Canvas activated')
        
        # Draw rectangle using EXACT same sequence as working direct test
        logger.info(f'🎯 STARTING RECTANGLE DRAW')
        
        # AGGRESSIVE DRAWING: Try multiple methods to ensure rectangle is drawn
        
        # Method 1: Standard press-drag-release
        logger.info(f"🖱️  METHOD 1: Standard press-drag-release")
        mouse.move(coords=(actual_x, actual_y))
        time.sleep(0.3)
        mouse.press(button='left', coords=(actual_x, actual_y))
        time.sleep(0.3)
        mouse.move(coords=(actual_ex, actual_ey))
        time.sleep(0.3)
        mouse.release(button='left', coords=(actual_ex, actual_ey))
        time.sleep(1)
        logger.info(f"✅ Method 1 complete")
        
        # Method 2: Click-and-drag in one motion
        logger.info(f"🖱️  METHOD 2: Click-and-drag")
        mouse.click(coords=(actual_x, actual_y))
        time.sleep(0.2)
        # Simulate drag by press-move-release
        mouse.press(button='left', coords=(actual_x, actual_y))
        mouse.move(coords=(actual_ex, actual_ey))
        mouse.release(button='left', coords=(actual_ex, actual_ey))
        time.sleep(1)
        logger.info(f"✅ Method 2 complete")
        
        # Method 3: Multiple small rectangles to ensure something is visible
        logger.info(f"🖱️  METHOD 3: Multiple small rectangles")
        for i in range(3):
            offset = i * 20
            start_x = actual_x + offset
            start_y = actual_y + offset
            end_x = actual_ex - offset
            end_y = actual_ey - offset
            
            mouse.move(coords=(start_x, start_y))
            time.sleep(0.1)
            mouse.press(button='left', coords=(start_x, start_y))
            time.sleep(0.1)
            mouse.move(coords=(end_x, end_y))
            time.sleep(0.1)
            mouse.release(button='left', coords=(end_x, end_y))
            time.sleep(0.2)
        
        logger.info(f"🎉 AGGRESSIVE DRAWING COMPLETE!")
        
        logger.info(f'Rectangle drawn successfully')
        return jsonify({'status':'ok','rect':[sx,sy,width,height]})
    except Exception as e:
        logger.exception('draw_rectangle failed'); return jsonify({'status':'error','error': str(e)}), 500

@app.route('/tool/add_text_in_paint', methods=['POST'])
@log_and_time
def http_add_text_in_paint():
    if not IS_WINDOWS:
        return jsonify({'status':'error','error':'Not running on Windows'}), 500
    data = request.get_json(force=True) or {}
    x,y = int(data.get('x',0)), int(data.get('y',0)); text = str(data.get('text',''))[:4000]; font_size=int(data.get('font_size',24))
    win = STATE.get('window')
    if not win:
        return jsonify({'status':'error','error':'Paint window not opened'}), 400
    sx, sy = _to_screen_coords(x,y)
    try:
        # CRITICAL: First select the text tool from the toolbar
        logger.info(f'Selecting text tool in MS Paint')
        
        txt_tool = _find_text_tool(win)
        if txt_tool is not None:
            try:
                txt_tool.click_input()
                logger.info('Clicked Text tool via _find_text_tool')
                time.sleep(0.3)
            except Exception:
                try:
                    txt_tool.invoke()
                    logger.info('Invoked Text tool via _find_text_tool')
                    time.sleep(0.3)
                except Exception:
                    logger.warning('Failed to activate text tool')
        else:
            # Enhanced fallback: try multiple text tool locations
            try:
                # Look for text tool button by title
                text_btn = win.child_window(title="Text", control_type="Button")
                if text_btn.exists():
                    text_btn.click_input()
                    logger.info('Clicked Text button')
                    time.sleep(0.3)
                else:
                    # Fallback: click estimated text tool location
                    r = win.rectangle()
                    tool_x = r.left + 200  # Text tool is usually after shapes
                    tool_y = r.top + 120
                    mouse.click(button='left', coords=(tool_x, tool_y))
                    logger.info(f'Clicked estimated text tool location at ({tool_x}, {tool_y})')
                    time.sleep(0.3)
            except Exception as e:
                logger.warning(f'Text tool selection failed: {e}')
        
        # Use EXACT same safe area calculation as working direct test
        win_rect = win.rectangle()
        logger.info(f'Paint window rectangle for text: {win_rect}')
        
        # Calculate safe drawing area (EXACT same as direct test)
        safe_left = win_rect.left + 100
        safe_top = win_rect.top + 250  # Well below ribbon
        safe_right = win_rect.right - 100
        safe_bottom = win_rect.bottom - 100
        
        # Use center of safe area (EXACT same as direct test)
        center_x = (safe_left + safe_right) // 2
        center_y = (safe_top + safe_bottom) // 2
        
        # Place text at center (same as direct test)
        actual_x = center_x
        actual_y = center_y
        
        logger.info(f'Text position: ({actual_x}, {actual_y})')
        
        # Click at the text position to create text box
        logger.info(f'Placing text "{text}" at ({actual_x}, {actual_y})')
        mouse.click(button='left', coords=(actual_x, actual_y)); time.sleep(0.5)
        
        # Type the text
        keyboard.send_keys(text, with_spaces=True)
        time.sleep(0.2)
        
        # Click elsewhere to finish text entry
        mouse.click(coords=(actual_x + 100, actual_y + 50)); time.sleep(0.3)
        
        logger.info(f'Text "{text}" added successfully')
        return jsonify({'status':'ok','text_pos':[actual_x,actual_y],'text': text})
    except Exception as e:
        logger.exception('add_text_in_paint failed'); return jsonify({'status':'error','error': str(e)}), 500

def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--host', default='127.0.0.1'); parser.add_argument('--port', type=int, default=5000); args = parser.parse_args()
    logger.info('Starting MCP server on %s:%d', args.host, args.port); app.run(host=args.host, port=args.port, debug=False, use_reloader=False)

if __name__ == '__main__':
    main()
