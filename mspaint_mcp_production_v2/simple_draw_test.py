#!/usr/bin/env python3
"""
SUPER SIMPLE MS Paint drawing test - NO complex logic, just DRAW!
"""
import time
import subprocess
from pywinauto import Application, mouse
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def simple_draw():
    """Just draw a rectangle and text - SIMPLE!"""
    
    # 1. Open Paint
    logger.info("🎨 Opening MS Paint...")
    subprocess.Popen(['mspaint.exe'])
    time.sleep(3)
    
    # 2. Connect to Paint
    logger.info("🔗 Connecting to Paint...")
    app = Application(backend="uia").connect(title_re=".*Paint.*")
    win = app.top_window()
    logger.info(f"✅ Connected to Paint: {win.window_text()}")
    
    # 3. Get window size
    rect = win.rectangle()
    logger.info(f"📐 Paint window: {rect}")
    
    # 4. Calculate SIMPLE coordinates - just use the middle of the window
    center_x = (rect.left + rect.right) // 2
    center_y = (rect.top + rect.bottom) // 2
    
    # Rectangle coordinates - 300x200 rectangle centered
    rect_left = center_x - 150
    rect_top = center_y - 100
    rect_right = center_x + 150
    rect_bottom = center_y + 100
    
    logger.info(f"🎯 Drawing rectangle: ({rect_left}, {rect_top}) to ({rect_right}, {rect_bottom})")
    
    # 5. Select rectangle tool (try multiple ways)
    logger.info("🔧 Selecting rectangle tool...")
    try:
        # Try to find rectangle button
        rect_btn = win.child_window(title="Rectangle", control_type="Button")
        if rect_btn.exists():
            rect_btn.click_input()
            logger.info("✅ Clicked Rectangle button")
        else:
            logger.info("❌ Rectangle button not found, trying shapes...")
            # Try shapes dropdown
            shapes = win.child_window(title="Shapes", control_type="Button")
            if shapes.exists():
                shapes.click_input()
                time.sleep(0.5)
                # Look for rectangle in dropdown
                rect_item = win.child_window(title="Rectangle", control_type="ListItem")
                if rect_item.exists():
                    rect_item.click_input()
                    logger.info("✅ Selected Rectangle from Shapes")
    except Exception as e:
        logger.warning(f"⚠️ Tool selection failed: {e}")
    
    time.sleep(1)
    
    # 6. Draw rectangle - SIMPLE drag operation
    logger.info("✏️ Drawing rectangle...")
    
    # Move to start position
    mouse.move(coords=(rect_left, rect_top))
    time.sleep(0.5)
    logger.info(f"📍 Moved to start: ({rect_left}, {rect_top})")
    
    # Press and drag
    mouse.press(button='left', coords=(rect_left, rect_top))
    time.sleep(0.3)
    logger.info("🖱️ Pressed mouse")
    
    # Drag to end
    mouse.move(coords=(rect_right, rect_bottom))
    time.sleep(0.5)
    logger.info(f"📍 Dragged to end: ({rect_right}, {rect_bottom})")
    
    # Release
    mouse.release(button='left', coords=(rect_right, rect_bottom))
    time.sleep(0.5)
    logger.info("🖱️ Released mouse")
    
    # 7. Add text
    logger.info("📝 Adding text...")
    
    # Select text tool
    try:
        text_btn = win.child_window(title="Text", control_type="Button")
        if text_btn.exists():
            text_btn.click_input()
            logger.info("✅ Clicked Text button")
        else:
            logger.info("❌ Text button not found")
    except Exception as e:
        logger.warning(f"⚠️ Text tool selection failed: {e}")
    
    time.sleep(1)
    
    # Click in center to place text
    text_x = center_x
    text_y = center_y
    logger.info(f"📍 Placing text at: ({text_x}, {text_y})")
    
    mouse.click(button='left', coords=(text_x, text_y))
    time.sleep(1)
    
    # Type text
    logger.info("⌨️ Typing 'HELLO WORLD'...")
    win.type_keys("HELLO WORLD", with_spaces=True)
    time.sleep(1)
    
    logger.info("🎉 DONE! Check Paint window for rectangle and text!")

if __name__ == "__main__":
    simple_draw()
