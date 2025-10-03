#!/usr/bin/env python3
"""
Direct test of MS Paint drawing without the full MCP system
This will help us isolate whether the drawing logic works
"""
import os
import time
import logging
from pywinauto import Application, mouse, keyboard

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_paint_drawing():
    """Test drawing directly in MS Paint"""
    try:
        # Open Paint
        logger.info("Opening MS Paint...")
        os.system('start mspaint')
        time.sleep(3)
        
        # Connect to Paint (get the first one if multiple exist)
        try:
            app = Application(backend="uia").connect(title_re=".*Paint.*")
            win = app.window(title_re=".*Paint.*")
        except Exception as e:
            logger.info(f"Multiple Paint windows found, connecting to the first one...")
            # Get all Paint windows and connect to the first
            import pywinauto.findwindows as fw
            paint_windows = fw.find_elements(title_re=".*Paint.*")
            if paint_windows:
                app = Application(backend="uia").connect(process=paint_windows[0].process_id)
                win = app.window(title_re=".*Paint.*")
            else:
                raise Exception("No Paint windows found")
        
        logger.info(f"Connected to Paint window: {win.window_text()}")
        
        # Get window rectangle
        win_rect = win.rectangle()
        logger.info(f"Paint window rectangle: {win_rect}")
        
        # Calculate safe drawing area (very conservative)
        safe_left = win_rect.left + 100
        safe_top = win_rect.top + 250  # Well below ribbon
        safe_right = win_rect.right - 100
        safe_bottom = win_rect.bottom - 100
        
        logger.info(f"Safe drawing area: ({safe_left}, {safe_top}) to ({safe_right}, {safe_bottom})")
        
        # Try to select rectangle tool
        logger.info("Attempting to select rectangle tool...")
        try:
            rect_tool = win.child_window(title="Rectangle", control_type="Button")
            if rect_tool.exists():
                rect_tool.click_input()
                logger.info("✅ Rectangle tool selected")
                time.sleep(1)
            else:
                logger.warning("❌ Rectangle tool not found")
        except Exception as e:
            logger.warning(f"❌ Could not select rectangle tool: {e}")
        
        # Test 1: Simple click in center
        center_x = (safe_left + safe_right) // 2
        center_y = (safe_top + safe_bottom) // 2
        
        logger.info(f"Test 1: Clicking at center ({center_x}, {center_y})")
        mouse.click(coords=(center_x, center_y))
        time.sleep(1)
        
        # Test 2: Draw a small rectangle
        rect_x1 = center_x - 100
        rect_y1 = center_y - 50
        rect_x2 = center_x + 100
        rect_y2 = center_y + 50
        
        logger.info(f"Test 2: Drawing rectangle from ({rect_x1}, {rect_y1}) to ({rect_x2}, {rect_y2})")
        
        # Move to start position
        mouse.move(coords=(rect_x1, rect_y1))
        time.sleep(0.5)
        logger.info(f"Moved to start position")
        
        # Press and drag
        mouse.press(button='left', coords=(rect_x1, rect_y1))
        time.sleep(0.2)
        logger.info(f"Pressed mouse button")
        
        # Drag to end
        mouse.move(coords=(rect_x2, rect_y2))
        time.sleep(0.5)
        logger.info(f"Dragged to end position")
        
        # Release
        mouse.release(button='left', coords=(rect_x2, rect_y2))
        time.sleep(0.5)
        logger.info(f"Released mouse button")
        
        # Test 3: Try text tool and add text
        logger.info("Test 3: Attempting to select text tool...")
        try:
            # Look for text tool
            text_tool = win.child_window(title="Text", control_type="Button")
            if text_tool.exists():
                text_tool.click_input()
                logger.info("✅ Text tool selected")
                time.sleep(1)
                
                # Click to place text
                text_x = center_x
                text_y = center_y + 20
                logger.info(f"Placing text at ({text_x}, {text_y})")
                mouse.click(coords=(text_x, text_y))
                time.sleep(0.5)
                
                # Type text
                keyboard.send_keys("TEST", with_spaces=True)
                logger.info("✅ Text typed")
                time.sleep(1)
                
            else:
                logger.warning("❌ Text tool not found")
        except Exception as e:
            logger.warning(f"❌ Could not use text tool: {e}")
        
        logger.info("🎉 Test completed! Check MS Paint to see if anything was drawn.")
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_paint_drawing()
    input("Press Enter to exit...")
