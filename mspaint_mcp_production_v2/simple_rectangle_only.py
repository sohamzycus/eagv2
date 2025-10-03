#!/usr/bin/env python3
"""
SUPER SIMPLE rectangle drawing test - NO complex logic, just draw ONE rectangle
"""
import time
import logging
from pywinauto import Application
from pywinauto import mouse

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def draw_simple_rectangle():
    """Draw ONE rectangle in Paint - SUPER SIMPLE approach"""
    try:
        logger.info("=== SUPER SIMPLE RECTANGLE TEST ===")
        
        # 1. Open Paint
        logger.info("Opening Paint...")
        app = Application().start("mspaint.exe")
        time.sleep(3)
        
        # 2. Connect to Paint window
        logger.info("Connecting to Paint...")
        paint_app = Application().connect(title_re=".*Paint.*")
        win = paint_app.window(title_re=".*Paint.*")
        win.set_focus()
        time.sleep(1)
        
        # 3. Get window size
        rect = win.rectangle()
        logger.info(f"Paint window: {rect}")
        
        # 4. Click Rectangle tool (try multiple ways)
        logger.info("Selecting Rectangle tool...")
        try:
            # Try to find rectangle button
            rect_btn = win.child_window(title="Rectangle", control_type="Button")
            if rect_btn.exists():
                rect_btn.click_input()
                logger.info("✅ Found and clicked Rectangle button")
            else:
                logger.info("❌ Rectangle button not found, trying coordinates...")
                # Click where rectangle tool usually is (left side of ribbon)
                tool_x = rect.left + 150
                tool_y = rect.top + 100
                mouse.click(coords=(tool_x, tool_y))
                logger.info(f"Clicked estimated rectangle tool at ({tool_x}, {tool_y})")
        except Exception as e:
            logger.warning(f"Rectangle tool selection failed: {e}")
        
        time.sleep(1)
        
        # 5. Draw rectangle with FIXED coordinates
        logger.info("Drawing rectangle with FIXED coordinates...")
        
        # Use FIXED coordinates that should work on any screen
        start_x = rect.left + 300   # 300px from left edge
        start_y = rect.top + 300    # 300px from top edge  
        end_x = rect.left + 600     # 600px from left edge
        end_y = rect.top + 500      # 500px from top edge
        
        logger.info(f"Rectangle: ({start_x}, {start_y}) to ({end_x}, {end_y})")
        
        # Draw the rectangle
        logger.info("Step 1: Move to start position")
        mouse.move(coords=(start_x, start_y))
        time.sleep(0.5)
        
        logger.info("Step 2: Press mouse button")
        mouse.press(button='left', coords=(start_x, start_y))
        time.sleep(0.3)
        
        logger.info("Step 3: Drag to end position")
        mouse.move(coords=(end_x, end_y))
        time.sleep(0.5)
        
        logger.info("Step 4: Release mouse button")
        mouse.release(button='left', coords=(end_x, end_y))
        time.sleep(1)
        
        logger.info("🎉 RECTANGLE DRAWING COMPLETE!")
        logger.info("Check Paint window - you should see a rectangle!")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ FAILED: {e}")
        return False

if __name__ == "__main__":
    success = draw_simple_rectangle()
    if success:
        print("\n✅ SUCCESS! Check Paint for the rectangle.")
    else:
        print("\n❌ FAILED! Check the logs above.")
    
    input("Press Enter to exit...")
